"""
Pipeline ETL puro: PocketBase crimes_220k -> MinIO (Parquet) + resumen materializado.

Sin generación ficticia. Extrae por paginación (streaming) y carga en segundo plano.
"""

from __future__ import annotations

from typing import Any, Callable

from core.etl.incremental_etl import (
    MAX_INCREMENTAL_BATCH,
    MIN_INCREMENTAL_BATCH,
    run_incremental_etl,
)
from core.etl.star_schema import run_etl_pb_to_minio
from core.services.minio_store import MinioParquetStore
from core.services.pocketbase import PocketBaseClient

ProgressFn = Callable[[dict[str, Any]], None]


def _minio_has_consolidated_fact() -> bool:
    store = MinioParquetStore()
    return store.has_consolidated_facts()


def resolve_sync_mode(mode: str) -> str:
    """auto -> incremental si ya hay fact en MinIO; si no, full."""
    normalized = (mode or "auto").strip().lower()
    if normalized == "auto":
        return "incremental" if _minio_has_consolidated_fact() else "full"
    if normalized not in ("incremental", "full"):
        raise ValueError("mode debe ser 'auto', 'incremental' o 'full'")
    return normalized


def validate_cantidad_registros(value: Any) -> int:
    """Valida el límite de carga incremental controlada (1 … 300_000)."""
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"cantidad_registros debe ser un entero entre "
            f"{MIN_INCREMENTAL_BATCH} y {MAX_INCREMENTAL_BATCH}"
        ) from exc
    if n < MIN_INCREMENTAL_BATCH or n > MAX_INCREMENTAL_BATCH:
        raise ValueError(
            f"cantidad_registros debe estar entre "
            f"{MIN_INCREMENTAL_BATCH} y {MAX_INCREMENTAL_BATCH} (recibido: {n})"
        )
    return n


def run_pocketbase_sync(
    *,
    mode: str = "auto",
    export_raw_copy: bool = True,
    per_page: int = 500,
    cantidad_registros: int | None = None,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """
    Extrae crimes_220k desde PocketBase y carga en MinIO (+ app_dashboard_summary).

    - incremental: solo registros nuevos (rápido).
    - full: reconstruye modelo estrella completo.
    - auto: elige incremental si MinIO ya tiene fact consolidado.
    """
    resolved = resolve_sync_mode(mode)

    if resolved == "incremental":
        limit = validate_cantidad_registros(
            cantidad_registros if cantidad_registros is not None else MAX_INCREMENTAL_BATCH
        )
        try:
            result = run_incremental_etl(
                cantidad_registros=limit,
                per_page=per_page,
                on_progress=on_progress,
            )
            result["sync_mode"] = "incremental"
            return result
        except ValueError as exc:
            if "No hay fact_crimes consolidado" not in str(exc):
                raise
            resolved = "full"

    result = run_etl_pb_to_minio(
        export_raw_copy=export_raw_copy,
        on_progress=on_progress,
    )
    result["sync_mode"] = "full"
    return result


def pocketbase_sync_stats() -> dict[str, Any]:
    """Conteos para la UI (PocketBase vs MinIO)."""
    with PocketBaseClient() as pb:
        pb.auth_admin()
        pb_count = pb.count_records("crimes_220k")

    store = MinioParquetStore()
    minio_fact = 0
    if store.has_consolidated_facts():
        from core.services.analytics_service import AnalyticsService

        minio_fact = AnalyticsService(store).count_fact_crimes()

    pending_estimate = max(0, pb_count - minio_fact)

    return {
        "pocketbase_crimes_220k": pb_count,
        "minio_fact_crimes": minio_fact,
        "minio_has_consolidated": store.has_consolidated_facts(),
        "recommended_mode": resolve_sync_mode("auto"),
        "pending_estimate": pending_estimate,
        "max_batch_size": MAX_INCREMENTAL_BATCH,
        "min_batch_size": MIN_INCREMENTAL_BATCH,
    }
