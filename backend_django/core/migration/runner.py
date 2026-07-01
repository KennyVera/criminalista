from __future__ import annotations

import time
from typing import Callable

import psycopg2
from django.conf import settings
from psycopg2.extras import RealDictCursor

from core.migration.postgres_config import (
    CRIMES_220K_COLUMNS,
    DIMENSION_MIGRATIONS,
    FACT_RELATIONS,
    DimensionMigration,
)
from core.migration.serializers import pg_value_to_pb
from core.services.pocketbase import PocketBaseClient, PocketBaseError

# Tamaño de lote hacia PocketBase (/api/batches) en migraciones masivas.
MIGRATION_PB_BATCH = 500


class PostgresMigrator:
    """
    ETL de un solo uso: PostgreSQL → PocketBase.
    No registra Postgres en settings.DATABASES de Django.
    """

    def __init__(
        self,
        pb: PocketBaseClient,
        *,
        batch_size: int = 200,
        skip_existing: bool = True,
        dry_run: bool = False,
        log: Callable[[str], None] | None = None,
    ):
        self.pb = pb
        self.batch_size = batch_size
        self.skip_existing = skip_existing
        self.dry_run = dry_run
        self.log = log or (lambda msg: None)
        self._legacy_maps: dict[str, dict[int, str]] = {}

    def connect_postgres(self):
        return psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
        )

    def load_legacy_map(self, collection: str) -> dict[int, str]:
        if collection in self._legacy_maps:
            return self._legacy_maps[collection]

        mapping: dict[int, str] = {}
        page = 1
        while True:
            data = self.pb.list_records(
                collection,
                page=page,
                per_page=500,
                sort="@rowid",
            )
            for item in data.get("items", []):
                legacy = item.get("legacy_id")
                if legacy is not None:
                    mapping[int(legacy)] = item["id"]
            total_pages = data.get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1

        self._legacy_maps[collection] = mapping
        return mapping

    def _row_to_body(
        self,
        row: dict,
        columns: dict[str, str],
        legacy_id: int,
    ) -> dict:
        body = {"legacy_id": legacy_id}
        for pg_col, pb_field in columns.items():
            value = pg_value_to_pb(row.get(pg_col))
            if value is not None:
                body[pb_field] = value
        return body

    def _pg_count(self, table: str) -> int | None:
        try:
            with self.connect_postgres() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    return int(cur.fetchone()[0])
        except Exception:
            return None

    def migrate_dimension(self, config: DimensionMigration) -> tuple[int, int, int]:
        existing = self.load_legacy_map(config.pb_collection) if self.skip_existing else {}
        created = skipped = errors = 0
        processed = 0
        t0 = time.time()

        total = self._pg_count(config.pg_table)
        if total is not None:
            self.log(f"  filas en Postgres: {total:,} (puede tardar varios minutos)")

        pg_cols = [config.pg_pk, *config.columns.keys()]
        col_list = ", ".join(pg_cols)
        query = f"SELECT {col_list} FROM {config.pg_table} ORDER BY {config.pg_pk}"

        with self.connect_postgres() as conn:
            with conn.cursor(name=f"mig_{config.pb_collection}", cursor_factory=RealDictCursor) as cur:
                cur.itersize = self.batch_size
                cur.execute(query)
                while True:
                    rows = cur.fetchmany(self.batch_size)
                    if not rows:
                        break
                    for row in rows:
                        processed += 1
                        legacy_id = int(row[config.pg_pk])
                        if legacy_id in existing:
                            skipped += 1
                        else:
                            body = self._row_to_body(row, config.columns, legacy_id)
                            if self.dry_run:
                                created += 1
                            else:
                                try:
                                    record = self.pb.create_record(config.pb_collection, body)
                                    existing[legacy_id] = record["id"]
                                    created += 1
                                except PocketBaseError as exc:
                                    errors += 1
                                    if errors <= 5:
                                        self.log(
                                            f"  ERROR {config.pb_collection} "
                                            f"legacy_id={legacy_id}: {exc}"
                                        )

                        if processed % 500 == 0:
                            elapsed = time.time() - t0
                            rate = processed / elapsed if elapsed else 0
                            pct = f" ({100 * processed / total:.1f}%)" if total else ""
                            self.log(
                                f"  … {processed:,}{pct} procesadas "
                                f"| creados={created:,} | ~{rate:.1f} filas/s"
                            )

        self._legacy_maps[config.pb_collection] = existing
        return created, skipped, errors

    def migrate_all_dimensions(self) -> dict[str, tuple[int, int, int]]:
        results = {}
        for config in DIMENSION_MIGRATIONS:
            self.log(f"→ {config.pg_table} → {config.pb_collection}")
            results[config.pb_collection] = self.migrate_dimension(config)
            c, s, e = results[config.pb_collection]
            self.log(f"  creados={c} omitidos={s} errores={e}")
        return results

    def migrate_fact_crimes(self) -> tuple[int, int, int]:
        dim_collections = {dim for _, dim in FACT_RELATIONS.values()}
        id_maps: dict[str, dict[int, str]] = {}
        for dim in dim_collections:
            id_maps[dim] = self.load_legacy_map(dim)

        existing_facts = self.load_legacy_map("fact_crimes") if self.skip_existing else {}
        created = skipped = errors = 0

        pg_cols = ["id_fact", *FACT_RELATIONS.keys()]
        col_list = ", ".join(pg_cols)
        query = f"SELECT {col_list} FROM fact_crimes ORDER BY id_fact"

        with self.connect_postgres() as conn:
            with conn.cursor(name="mig_fact_crimes", cursor_factory=RealDictCursor) as cur:
                cur.itersize = self.batch_size
                cur.execute(query)
                processed = 0
                while True:
                    rows = cur.fetchmany(self.batch_size)
                    if not rows:
                        break
                    for row in rows:
                        legacy_id = int(row["id_fact"])
                        if legacy_id in existing_facts:
                            skipped += 1
                            continue

                        body: dict = {"legacy_id": legacy_id}
                        skip_row = False
                        for pg_fk, (pb_field, dim_collection) in FACT_RELATIONS.items():
                            fk_val = row.get(pg_fk)
                            if fk_val is None:
                                continue
                            pb_id = id_maps[dim_collection].get(int(fk_val))
                            if not pb_id:
                                skip_row = True
                                break
                            body[pb_field] = pb_id

                        if skip_row:
                            errors += 1
                            continue

                        if self.dry_run:
                            created += 1
                        else:
                            try:
                                record = self.pb.create_record("fact_crimes", body)
                                existing_facts[legacy_id] = record["id"]
                                created += 1
                            except PocketBaseError:
                                errors += 1

                        processed += 1
                        if processed % 5000 == 0:
                            self.log(f"  fact_crimes procesados: {processed}...")

        return created, skipped, errors

    def _load_existing_crime_ids(self) -> set[str]:
        """IDs ya presentes en PocketBase crimes_220k (campo id de negocio)."""
        existing: set[str] = set()
        self.log("  Cargando IDs existentes en PocketBase crimes_220k…")
        t0 = time.time()
        for item in self.pb.iter_records("crimes_220k", per_page=500, fields="id"):
            raw_id = item.get("id")
            if raw_id is not None and str(raw_id).strip():
                existing.add(str(raw_id))
        elapsed = time.time() - t0
        self.log(f"  IDs en PocketBase: {len(existing):,} ({elapsed:.1f}s)")
        return existing

    def _row_to_crimes_body(self, row: dict) -> dict:
        body: dict = {}
        for pg_col, pb_field in CRIMES_220K_COLUMNS.items():
            value = pg_value_to_pb(row.get(pg_col))
            if value is not None:
                body[pb_field] = value
        return body

    def _flush_crimes_batch(
        self,
        collection: str,
        bodies: list[dict],
    ) -> tuple[int, int]:
        if not bodies:
            return 0, 0
        if self.dry_run:
            return len(bodies), 0
        created, errors, _ = self.pb.create_records_batch(collection, bodies)
        return created, errors

    def migrate_crimes_from_postgres(
        self,
        pg_table: str,
        *,
        limit: int | None = None,
    ) -> tuple[int, int, int]:
        """
        Migra filas de una tabla plana Postgres (crimes_220k, public.crimes_2m, …)
        hacia PocketBase crimes_220k, omitiendo IDs ya presentes.

        limit: máximo de registros NUEVOS a crear (None = sin tope).
        """
        existing = self._load_existing_crime_ids() if self.skip_existing else set()
        created = skipped = errors = 0
        pg_cols = list(CRIMES_220K_COLUMNS.keys())
        col_list = ", ".join(pg_cols)
        query = f"SELECT {col_list} FROM {pg_table} ORDER BY id"

        total_pg = self._pg_count(pg_table)
        if total_pg is not None:
            self.log(f"  Filas en Postgres ({pg_table}): {total_pg:,}")
        if limit:
            self.log(f"  Objetivo: hasta {limit:,} registros nuevos en PocketBase")

        pending: list[dict] = []
        processed = 0
        t0 = time.time()

        with self.connect_postgres() as conn:
            with conn.cursor(name=f"mig_{pg_table.replace('.', '_')}", cursor_factory=RealDictCursor) as cur:
                cur.itersize = self.batch_size
                cur.execute(query)
                while True:
                    if limit is not None and created >= limit:
                        break
                    rows = cur.fetchmany(self.batch_size)
                    if not rows:
                        break
                    for row in rows:
                        if limit is not None and created >= limit:
                            break
                        processed += 1
                        row_id = row.get("id")
                        row_key = str(row_id) if row_id is not None else ""
                        if row_key and row_key in existing:
                            skipped += 1
                            continue

                        pending.append(self._row_to_crimes_body(row))
                        if row_key:
                            existing.add(row_key)

                        if len(pending) >= MIGRATION_PB_BATCH:
                            c, e = self._flush_crimes_batch("crimes_220k", pending)
                            created += c
                            errors += e
                            pending.clear()
                            if limit is not None and created >= limit:
                                break

                        if processed % 10000 == 0:
                            elapsed = time.time() - t0
                            rate = processed / elapsed if elapsed else 0
                            self.log(
                                f"  {pg_table}: {processed:,} leídas "
                                f"({rate:.0f}/s) creados={created:,} omitidos={skipped:,} errores={errors}"
                            )

        if pending and (limit is None or created < limit):
            if limit is not None:
                pending = pending[: max(0, limit - created)]
            c, e = self._flush_crimes_batch("crimes_220k", pending)
            created += c
            errors += e

        return created, skipped, errors

    def migrate_crimes_220k(self) -> tuple[int, int, int]:
        return self.migrate_crimes_from_postgres("crimes_220k")

    def migrate_crimes_2m(self, limit: int = 1_000_000) -> tuple[int, int, int]:
        return self.migrate_crimes_from_postgres("public.crimes_2m", limit=limit)
