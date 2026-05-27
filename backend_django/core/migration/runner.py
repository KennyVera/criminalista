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

    def migrate_crimes_220k(self) -> tuple[int, int, int]:
        existing: set[str] = set()
        if self.skip_existing:
            page = 1
            while True:
                data = self.pb.list_records("crimes_220k", page=page, per_page=500, sort="@rowid")
                for item in data.get("items", []):
                    if item.get("id"):
                        existing.add(str(item["id"]))
                if page >= data.get("totalPages", 1):
                    break
                page += 1

        created = skipped = errors = 0
        pg_cols = list(CRIMES_220K_COLUMNS.keys())
        col_list = ", ".join(pg_cols)
        query = f"SELECT {col_list} FROM crimes_220k"

        with self.connect_postgres() as conn:
            with conn.cursor(name="mig_crimes_220k", cursor_factory=RealDictCursor) as cur:
                cur.itersize = self.batch_size
                cur.execute(query)
                processed = 0
                t0 = time.time()
                while True:
                    rows = cur.fetchmany(self.batch_size)
                    if not rows:
                        break
                    for row in rows:
                        row_id = row.get("id")
                        if row_id is not None and str(row_id) in existing:
                            skipped += 1
                            continue

                        body = {}
                        for pg_col, pb_field in CRIMES_220K_COLUMNS.items():
                            value = pg_value_to_pb(row.get(pg_col))
                            if value is not None:
                                body[pb_field] = value

                        if self.dry_run:
                            created += 1
                        else:
                            try:
                                self.pb.create_record("crimes_220k", body)
                                created += 1
                                if row_id is not None:
                                    existing.add(str(row_id))
                            except PocketBaseError:
                                errors += 1

                        processed += 1
                        if processed % 10000 == 0:
                            elapsed = time.time() - t0
                            rate = processed / elapsed if elapsed else 0
                            self.log(
                                f"  crimes_220k: {processed} filas "
                                f"({rate:.0f}/s) creados={created} errores={errors}"
                            )

        return created, skipped, errors
