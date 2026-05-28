"""
ETL: crimes_220k (PocketBase) → modelo estrella Parquet → MinIO.

1. Extraer dataset crudo desde PocketBase (paginas en paralelo)
2. Transformar a dimensiones + fact_crimes (mapeo FK vectorizado)
3. Persistir como .parquet en MinIO (capa analítica)
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable

import pandas as pd

from core.etl.dim_enrichment import enrich_all_dimensions
from core.etl.fast_keys import as_merge_str, composite_key, map_foreign_key
from core.etl.parquet_partition import write_partitioned_fact_crimes
from core.etl.pb_fetch import fetch_crimes_220k_parallel
from core.services.minio_store import DIM_COLLECTIONS, MinioParquetStore
from core.services.pocketbase import PocketBaseClient

ProgressFn = Callable[[dict[str, Any]], None]


def _emit(on_progress: ProgressFn | None, **kwargs: Any) -> None:
    if on_progress:
        on_progress(kwargs)


def _unique_dim(df: pd.DataFrame, cols: list[str], key_cols: list[str]) -> pd.DataFrame:
    """Filas unicas para una dimensión; asigna id entero."""
    subset = df[cols].copy()
    for c in subset.columns:
        subset[c] = as_merge_str(subset[c])
    subset = subset.drop_duplicates(subset=key_cols, keep="first").reset_index(drop=True)
    subset.insert(0, "id", range(1, len(subset) + 1))
    return subset


def _build_dimensions(raw_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construye dimensiones a partir del dataset plano."""
    dims: dict[str, pd.DataFrame] = {}

    dims["dim_caso"] = _unique_dim(raw_df, ["case_number"], ["case_number"])
    dims["dim_caso"]["estado_caso"] = "Importado"
    dims["dim_caso"]["prioridad_caso"] = "Media"

    dims["dim_tipo_crimen"] = _unique_dim(
        raw_df,
        ["iucr", "primary_type", "description", "fbi_code"],
        ["iucr", "primary_type"],
    )

    dims["dim_distrito_policial"] = _unique_dim(
        raw_df,
        ["beat", "district"],
        ["beat", "district"],
    )

    dims["dim_area_administrativa"] = _unique_dim(
        raw_df,
        ["ward", "community_area"],
        ["ward", "community_area"],
    )

    dims["dim_tiempo"] = _unique_dim(raw_df, ["date", "year"], ["date"])

    dims["dim_ubicacion_lugar"] = _unique_dim(
        raw_df,
        ["location_description", "block"],
        ["location_description", "block"],
    )

    geo_cols = ["latitude", "longitude", "location"]
    for c in ("x_coordinate", "y_coordinate"):
        if c in raw_df.columns:
            geo_cols.append(c)
    dims["dim_ubicacion_geografica"] = _unique_dim(
        raw_df,
        geo_cols,
        ["latitude", "longitude"],
    )

    dims["dim_arresto"] = _unique_dim(raw_df, ["arrest"], ["arrest"])
    dims["dim_violencia_domestica"] = _unique_dim(raw_df, ["domestic"], ["domestic"])
    dims["dim_actualizacion"] = _unique_dim(raw_df, ["updated_on"], ["updated_on"])

    return dims


def _build_fact(raw_df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    raw = raw_df.copy()
    fk_cols = [c for c in raw.columns if c.startswith("fk_")]
    if fk_cols:
        raw = raw.drop(columns=fk_cols, errors="ignore")

    n = len(raw)
    fact = pd.DataFrame(
        {
            "id": pd.Series(range(1, n + 1), dtype="int64"),
            "raw_row_id": as_merge_str(raw.get("id", pd.Series(range(1, n + 1)))),
            "fk_caso": map_foreign_key(raw, dims["dim_caso"], ["case_number"], ["case_number"]),
            "fk_tipo_crimen": map_foreign_key(
                raw, dims["dim_tipo_crimen"], ["iucr", "primary_type"], ["iucr", "primary_type"]
            ),
            "fk_distrito": map_foreign_key(
                raw, dims["dim_distrito_policial"], ["beat", "district"], ["beat", "district"]
            ),
            "fk_area": map_foreign_key(
                raw,
                dims["dim_area_administrativa"],
                ["ward", "community_area"],
                ["ward", "community_area"],
            ),
            "fk_tiempo": map_foreign_key(raw, dims["dim_tiempo"], ["date"], ["date"]),
            "fk_ubicacion_lugar": map_foreign_key(
                raw,
                dims["dim_ubicacion_lugar"],
                ["location_description", "block"],
                ["location_description", "block"],
            ),
            "fk_ubicacion_geo": map_foreign_key(
                raw,
                dims["dim_ubicacion_geografica"],
                ["latitude", "longitude"],
                ["latitude", "longitude"],
            ),
            "fk_arresto": map_foreign_key(raw, dims["dim_arresto"], ["arrest"], ["arrest"]),
            "fk_domestico": map_foreign_key(
                raw, dims["dim_violencia_domestica"], ["domestic"], ["domestic"]
            ),
            "fk_actualizacion": map_foreign_key(
                raw, dims["dim_actualizacion"], ["updated_on"], ["updated_on"]
            ),
        }
    )

    for col in fact.columns:
        if col.startswith("fk_"):
            fact[col] = pd.to_numeric(fact[col], errors="coerce").astype("Int64")

    return fact


def _should_skip_raw_export(row_count: int, export_raw_copy: bool) -> bool:
    if not export_raw_copy:
        return True
    if os.getenv("ETL_SKIP_RAW_EXPORT", "").lower() in ("1", "true", "yes"):
        return True
    return row_count > int(os.getenv("ETL_RAW_EXPORT_MAX_ROWS", "50000"))


def run_etl_pb_to_minio(
    *,
    export_raw_copy: bool = True,
    on_progress: ProgressFn | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """
    Pipeline ETL completo según requisitos 1–3:
      1. Extraer crimes_220k desde PocketBase
      2. Convertir a Parquet (dims + fact)
      3. Cargar en MinIO
    """
    def _abort_if_cancelled() -> None:
        if should_cancel and should_cancel():
            raise RuntimeError("ETL cancelado por el usuario.")

    t0 = time.time()
    _abort_if_cancelled()
    _emit(on_progress, phase="extract", percent=5, message="Extrayendo crimes_220k...")

    with PocketBaseClient() as pb:
        pb.auth_admin()
        raw_items = fetch_crimes_220k_parallel(pb)

    _abort_if_cancelled()

    if not raw_items:
        raise ValueError(
            "No hay registros en crimes_220k (PocketBase). "
            "Ejecuta migrate_from_postgres --steps raw primero."
        )

    raw_df = pd.DataFrame(raw_items)
    # Columnas PB internas que no aportan al modelo
    raw_df = raw_df.drop(
        columns=[c for c in raw_df.columns if c in ("collectionId", "collectionName", "expand")],
        errors="ignore",
    )

    _emit(
        on_progress,
        phase="transform",
        percent=25,
        message=f"Transformando {len(raw_df):,} filas...".replace(",", "."),
        raw_rows=len(raw_df),
    )

    _abort_if_cancelled()
    dims = enrich_all_dimensions(_build_dimensions(raw_df))
    fact_df = _build_fact(raw_df, dims)

    _abort_if_cancelled()
    _emit(on_progress, phase="upload", percent=60, message="Subiendo Parquet a MinIO...")

    store = MinioParquetStore()
    summary: dict[str, Any] = {"collections": {}, "raw_rows": len(raw_df)}

    skip_raw = _should_skip_raw_export(len(raw_df), export_raw_copy)
    if not skip_raw:
        raw_export = raw_df.copy()
        if "id" not in raw_export.columns:
            raw_export.insert(0, "id", range(1, len(raw_export) + 1))
        store.write_df("crimes_220k", raw_export)
        summary["collections"]["crimes_220k"] = len(raw_export)
    else:
        summary["raw_export_skipped"] = True

    for i, name in enumerate(DIM_COLLECTIONS):
        _abort_if_cancelled()
        store.write_df(name, dims[name])
        summary["collections"][name] = len(dims[name])
        pct = 60 + int(25 * (i + 1) / len(DIM_COLLECTIONS))
        _emit(on_progress, phase="upload", percent=pct, message=f"Dimension {name} lista.")

    _abort_if_cancelled()
    partition_meta = write_partitioned_fact_crimes(store, fact_df, dims)
    summary["collections"]["fact_crimes"] = partition_meta["rows"]
    summary["fact_partitioning"] = partition_meta
    summary["elapsed_seconds"] = round(time.time() - t0, 2)

    _emit(on_progress, phase="done", percent=100, message="ETL completado.")

    return {
        "success": True,
        "message": (
            f"ETL completado en {summary['elapsed_seconds']}s: {len(raw_df)} filas crudas -> "
            f"{partition_meta['rows']} hechos en {partition_meta['partitions']} particiones "
            f"(year/month) y {len(DIM_COLLECTIONS)} dimensiones en MinIO."
        ),
        **summary,
    }
