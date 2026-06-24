"""
Inserción masiva en crimes_220k (PocketBase) con UNICIDAD garantizada.

Garantías:
- `id`: 13 dígitos → nunca colisiona con los existentes (≤10 dígitos) ni entre sí.
- `case_number`: «JK» + 7 dígitos → nunca colisiona con los existentes
  («JK» + 6 dígitos) ni entre sí.
Además, se precargan las claves existentes desde MinIO (DuckDB, best-effort) y se
deduplica en memoria durante toda la corrida. No ejecuta ETL: inserta solo en
PocketBase (el modelo estrella se materializa aparte con etl_pb_to_minio).
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable

from core.services.faker_realistic import (
    HISTORICAL_YEAR_WEIGHTS,
    HISTORICAL_YEARS,
    gen_crimes_220k_for_year,
    resolve_gap_fill_weights,
)
from core.services.faker_seed import (
    DEFAULT_WORKERS,
    DISTRICTS,
    _DISTRICT_WEIGHTS,
    _fake,
)
from core.services.pocketbase import PocketBaseClient, PocketBaseError

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict[str, Any]], None]

# Rangos diseñados para no solapar con el dataset existente.
_ID_MIN = 1_000_000_000_000  # 13 dígitos
_ID_MAX = 9_999_999_999_999
_CASE_MIN = 1_000_000  # «JK» + 7 dígitos
_CASE_MAX = 9_999_999

# Tamaño del lote enviado al endpoint /api/batches (1 transacción SQLite c/u).
PB_BATCH_SIZE = 250


def _load_existing_keys() -> tuple[set[str], set[str]]:
    """Lee (id, case_number) existentes desde el Parquet de MinIO vía DuckDB."""
    ids: set[str] = set()
    cases: set[str] = set()
    try:
        from core.services.analytics_service import AnalyticsService
        from core.services.minio_store import MinioParquetStore

        store = MinioParquetStore()
        analytics = AnalyticsService(store)
        con = analytics.connection()
        src = analytics._s3_uri(store._object_key("crimes_220k"))
        try:
            con.execute(f"SELECT 1 FROM read_parquet('{src}') LIMIT 1").fetchone()
        except Exception:
            return ids, cases
        rows = con.execute(
            f"""
            SELECT CAST(id AS VARCHAR) AS id, CAST(case_number AS VARCHAR) AS cn
            FROM read_parquet('{src}')
            """
        ).fetchall()
        for rid, cn in rows:
            if rid:
                ids.add(str(rid))
            if cn:
                cases.add(str(cn))
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("No se pudieron precargar claves existentes: %s", exc)
    return ids, cases


def _make_unique_factory(used_ids: set[str], used_cases: set[str]):
    def _unique_id() -> str:
        while True:
            candidate = str(random.randint(_ID_MIN, _ID_MAX))
            if candidate not in used_ids:
                used_ids.add(candidate)
                return candidate

    def _unique_case() -> str:
        while True:
            candidate = f"JK{random.randint(_CASE_MIN, _CASE_MAX)}"
            if candidate not in used_cases:
                used_cases.add(candidate)
                return candidate

    return _unique_id, _unique_case


def bulk_insert_unique_crimes(
    total_count: int,
    *,
    workers: int = DEFAULT_WORKERS,
    on_progress: ProgressCallback | None = None,
    gap_fill: bool = True,
    prefill_existing: bool = True,
) -> dict[str, Any]:
    """Inserta N registros únicos en crimes_220k (solo PocketBase, sin ETL)."""
    if total_count < 1:
        raise ValueError("total_count debe ser >= 1")

    used_ids: set[str] = set()
    used_cases: set[str] = set()
    prefilled = 0
    if prefill_existing:
        used_ids, used_cases = _load_existing_keys()
        prefilled = len(used_ids)
    unique_id, unique_case = _make_unique_factory(used_ids, used_cases)

    gap_meta: dict[str, Any] | None = None
    if gap_fill:
        gap_meta = resolve_gap_fill_weights()
        year_choices = gap_meta["year_choices"]
        year_weights = gap_meta["year_weights"]
        district_choices = gap_meta["district_choices"]
        district_weights = gap_meta["district_weights"]
    else:
        year_choices = HISTORICAL_YEARS
        year_weights = HISTORICAL_YEAR_WEIGHTS
        district_choices = DISTRICTS
        district_weights = _DISTRICT_WEIGHTS

    del workers  # SQLite serializa escrituras: se usa 1 hilo con lotes transaccionales.
    years_plan = random.choices(year_choices, weights=year_weights, k=total_count)
    districts_plan = random.choices(district_choices, weights=district_weights, k=total_count)
    year_histogram: dict[int, int] = {}
    for y in years_plan:
        year_histogram[y] = year_histogram.get(y, 0) + 1

    created = 0
    errors = 0
    samples: list[dict] = []
    error_messages: list[str] = []
    t0 = time.time()
    fake = _fake()

    with PocketBaseClient() as pb:
        pb.auth_admin()
        for offset in range(0, total_count, PB_BATCH_SIZE):
            chunk_size = min(PB_BATCH_SIZE, total_count - offset)
            bodies = []
            for i in range(chunk_size):
                year = years_plan[offset + i]
                dist = districts_plan[offset + i]
                body = gen_crimes_220k_for_year(fake, year, district=dist)
                body["id"] = unique_id()
                body["case_number"] = unique_case()
                bodies.append(body)

            try:
                c, e, chunk_samples = pb.create_records_batch("crimes_220k", bodies)
            except PocketBaseError as exc:
                c, e, chunk_samples = 0, len(bodies), []
                if len(error_messages) < 5 and str(exc) not in error_messages:
                    error_messages.append(str(exc))
            created += c
            errors += e
            for s in chunk_samples:
                if len(samples) < 8:
                    samples.append(s)

            if on_progress:
                done = offset + chunk_size
                on_progress(
                    {
                        "done": done,
                        "total": total_count,
                        "created": created,
                        "errors": errors,
                        "percent": round(100 * done / total_count, 1),
                        "last_sample": samples[-1] if samples else None,
                    }
                )

    elapsed = round(time.time() - t0, 2)
    return {
        "success": created > 0,
        "partial": created > 0 and errors > 0,
        "created": created,
        "errors": errors,
        "requested": total_count,
        "elapsed_seconds": elapsed,
        "prefilled_existing_keys": prefilled,
        "year_distribution": {str(k): v for k, v in sorted(year_histogram.items())},
        "samples": samples,
        "error_messages": error_messages,
        "message": (
            f"Se insertaron {created}/{total_count} registros únicos en crimes_220k "
            f"(PocketBase). Errores: {errors}."
        ),
        "hint_etl": "python manage.py etl_pb_to_minio",
    }
