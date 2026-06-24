"""
ETL incremental: agrega SOLO los registros nuevos de crimes_220k (PocketBase) al
modelo estrella en MinIO, sin reconstruir todo.

Estrategia:
  1. Lee el fact consolidado (latest.parquet) → raw_row_id ya procesados + max(id).
  2. Extrae de PocketBase solo los registros cuyo id no está en el fact (los nuevos),
     recorriendo por @rowid descendente (los nuevos son los últimos insertados).
  3. Calcula los miembros NUEVOS de cada dimensión (continuando los ids existentes),
     los enriquece y los anexa a cada dimensión.
  4. Construye los hechos de los nuevos registros (ids continuando max(id)) y los
     anexa al fact consolidado.
  5. Re-materializa el resumen del dashboard e invalida la caché.

El dashboard (DuckDB) lee únicamente fact_crimes/consolidated/latest.parquet y un
Parquet por dimensión, por lo que el append es consistente sin duplicar lecturas.
"""

from __future__ import annotations

import io
import time
from typing import Any, Callable

import pandas as pd

from core.etl.dim_enrichment import ENRICHERS, _add_legacy_id
from core.etl.fast_keys import as_merge_str, composite_key
from core.etl.streaming_fact_writer import _build_fact_chunk
from core.services.minio_store import DIM_COLLECTIONS, MinioParquetStore
from core.services.pocketbase import PocketBaseClient

ProgressFn = Callable[[dict[str, Any]], None]

_PB_DROP_COLS = frozenset({"collectionId", "collectionName", "expand"})

# (cols naturales, columnas clave, defaults) — espejo de IncrementalDimStore.
DIM_SPECS: dict[str, tuple[list[str], list[str], dict[str, Any]]] = {
    "dim_caso": (["case_number"], ["case_number"], {"estado_caso": "Importado", "prioridad_caso": "Media"}),
    "dim_tipo_crimen": (["iucr", "primary_type", "description", "fbi_code"], ["iucr", "primary_type"], {}),
    "dim_distrito_policial": (["beat", "district"], ["beat", "district"], {}),
    "dim_area_administrativa": (["ward", "community_area"], ["ward", "community_area"], {}),
    "dim_tiempo": (["date", "year"], ["date"], {}),
    "dim_ubicacion_lugar": (["location_description", "block"], ["location_description", "block"], {}),
    "dim_arresto": (["arrest"], ["arrest"], {}),
    "dim_violencia_domestica": (["domestic"], ["domestic"], {}),
    "dim_actualizacion": (["updated_on"], ["updated_on"], {}),
    "dim_ubicacion_geografica": (["latitude", "longitude", "location"], ["latitude", "longitude"], {}),
}


def _emit(on_progress: ProgressFn | None, **kwargs: Any) -> None:
    if on_progress:
        on_progress(kwargs)


def _read_consolidated_fact(store: MinioParquetStore) -> pd.DataFrame:
    key = store.fact_crimes_consolidated_key()
    try:
        obj = store._client.get_object(Bucket=store.bucket, Key=key)
        return pd.read_parquet(io.BytesIO(obj["Body"].read()))
    except Exception:
        return pd.DataFrame()


def _write_consolidated_fact(store: MinioParquetStore, df: pd.DataFrame) -> None:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, compression="snappy")
    buffer.seek(0)
    store._client.put_object(
        Bucket=store.bucket,
        Key=store.fact_crimes_consolidated_key(),
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    store.invalidate_cache("fact_crimes")


def _extract_new_records(
    pb: PocketBaseClient,
    existing_ids: set[str],
    *,
    per_page: int = 500,
    stop_streak: int = 2000,
    on_progress: ProgressFn | None = None,
) -> list[dict[str, Any]]:
    """Recorre crimes_220k por @rowid descendente y junta los no presentes en el fact."""
    new_records: list[dict[str, Any]] = []
    consecutive_existing = 0
    scanned = 0
    for rec in pb.iter_records("crimes_220k", per_page=per_page, sort="-@rowid"):
        scanned += 1
        rid = str(rec.get("id"))
        if rid in existing_ids:
            consecutive_existing += 1
            if consecutive_existing >= stop_streak:
                break
            continue
        consecutive_existing = 0
        new_records.append(rec)
        if on_progress and len(new_records) % 5000 == 0:
            _emit(
                on_progress,
                phase="extract",
                message=f"Nuevos detectados: {len(new_records):,}".replace(",", "."),
                new_count=len(new_records),
                scanned=scanned,
            )
    return new_records


def _records_to_df(records: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    return df.drop(columns=[c for c in df.columns if c in _PB_DROP_COLS], errors="ignore")


def _new_dim_members(
    new_raw: pd.DataFrame,
    existing_dim: pd.DataFrame,
    cols: list[str],
    key_cols: list[str],
    defaults: dict[str, Any],
) -> pd.DataFrame:
    """Miembros de dimensión presentes en los nuevos registros y no en la dim existente."""
    cols_present = [c for c in cols if c in new_raw.columns]
    if not all(k in cols_present for k in key_cols):
        return pd.DataFrame()
    subset = new_raw[cols_present].copy()
    for col in subset.columns:
        subset[col] = as_merge_str(subset[col])
    subset = subset.drop_duplicates(subset=key_cols, keep="first").reset_index(drop=True)

    if existing_dim.empty:
        existing_keys: set[str] = set()
        max_id = 0
    else:
        existing_keys = set(composite_key(existing_dim, key_cols))
        max_id = int(pd.to_numeric(existing_dim["id"], errors="coerce").max())

    keys = composite_key(subset, key_cols)
    new_members = subset[~keys.isin(existing_keys)].reset_index(drop=True)
    if new_members.empty:
        return pd.DataFrame()

    new_members.insert(0, "id", range(max_id + 1, max_id + 1 + len(new_members)))
    for k, v in defaults.items():
        new_members[k] = v
    return new_members


def run_incremental_etl(
    *,
    per_page: int = 500,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    t0 = time.time()
    store = MinioParquetStore()

    _emit(on_progress, phase="read", percent=2, message="Leyendo fact consolidado en MinIO...")
    fact_df = _read_consolidated_fact(store)
    if fact_df.empty:
        raise ValueError(
            "No hay fact_crimes consolidado en MinIO. Ejecuta primero el ETL completo "
            "(python manage.py etl_pb_to_minio)."
        )
    existing_ids = set(as_merge_str(fact_df["raw_row_id"]))
    max_fact_id = int(pd.to_numeric(fact_df["id"], errors="coerce").max())

    _emit(
        on_progress,
        phase="extract",
        percent=8,
        message=f"Fact actual: {len(fact_df):,} filas. Buscando nuevos en PocketBase...".replace(",", "."),
    )

    with PocketBaseClient() as pb:
        pb.auth_admin()
        new_records = _extract_new_records(pb, existing_ids, per_page=per_page, on_progress=on_progress)

    if not new_records:
        return {
            "success": True,
            "new_records": 0,
            "elapsed_seconds": round(time.time() - t0, 2),
            "message": "No hay registros nuevos en PocketBase respecto a MinIO. Nada que hacer.",
        }

    new_raw = _records_to_df(new_records)
    n_new = len(new_raw)
    _emit(
        on_progress,
        phase="transform",
        percent=45,
        message=f"{n_new:,} registros nuevos. Calculando dimensiones...".replace(",", "."),
        new_count=n_new,
    )

    # Soporte de columnas geo opcionales (x/y) como en el pipeline completo.
    geo_cols = ["latitude", "longitude", "location"]
    for extra in ("x_coordinate", "y_coordinate"):
        if extra in new_raw.columns:
            geo_cols.append(extra)
    specs = dict(DIM_SPECS)
    specs["dim_ubicacion_geografica"] = (geo_cols, ["latitude", "longitude"], {})

    dims_for_fact: dict[str, pd.DataFrame] = {}
    dim_appends: dict[str, dict[str, Any]] = {}

    for name in DIM_COLLECTIONS:
        cols, key_cols, defaults = specs[name]
        existing_dim = store.read_df(name, use_cache=False)
        new_members = _new_dim_members(new_raw, existing_dim, cols, key_cols, defaults)

        if new_members.empty:
            dims_for_fact[name] = (
                existing_dim[key_cols + ["id"]] if not existing_dim.empty else pd.DataFrame(columns=key_cols + ["id"])
            )
            dim_appends[name] = {"new": 0, "total": len(existing_dim)}
            continue

        # FK lookup combinado (claves naturales + id), sin enriquecer.
        base_existing = existing_dim[key_cols + ["id"]] if not existing_dim.empty else pd.DataFrame(columns=key_cols + ["id"])
        dims_for_fact[name] = pd.concat(
            [base_existing, new_members[key_cols + ["id"]]], ignore_index=True
        )

        enricher = ENRICHERS.get(name)
        enriched_new = enricher(new_members) if enricher else _add_legacy_id(new_members)
        updated_dim = pd.concat([existing_dim, enriched_new], ignore_index=True)
        store.write_df(name, updated_dim)
        dim_appends[name] = {"new": len(new_members), "total": len(updated_dim)}
        _emit(
            on_progress,
            phase="upload",
            message=f"{name}: +{len(new_members):,} (total {len(updated_dim):,})".replace(",", "."),
        )

    _emit(on_progress, phase="transform", percent=80, message="Construyendo hechos nuevos...")
    new_fact = _build_fact_chunk(new_raw, dims_for_fact, start_id=max_fact_id + 1)
    new_fact = new_fact.drop(columns=[c for c in new_fact.columns if c in ("year", "month")], errors="ignore")

    updated_fact = pd.concat([fact_df, new_fact], ignore_index=True)
    _emit(
        on_progress,
        phase="upload",
        percent=92,
        message=f"Anexando {len(new_fact):,} hechos → {len(updated_fact):,} totales...".replace(",", "."),
    )
    _write_consolidated_fact(store, updated_fact)

    _emit(on_progress, phase="done", percent=98, message="Re-materializando resumen del dashboard...")
    from core.services.analytics_service import invalidate_dashboard_cache
    from packages.dashboard_analitica.services.summary_materializer import (
        materialize_dashboard_summary,
    )

    materialize_dashboard_summary()
    invalidate_dashboard_cache()

    elapsed = round(time.time() - t0, 2)
    return {
        "success": True,
        "new_records": n_new,
        "fact_before": len(fact_df),
        "fact_after": len(updated_fact),
        "dimensions": dim_appends,
        "elapsed_seconds": elapsed,
        "message": (
            f"ETL incremental: +{n_new} hechos (fact {len(fact_df)} → {len(updated_fact)}) "
            f"en {elapsed}s."
        ),
    }
