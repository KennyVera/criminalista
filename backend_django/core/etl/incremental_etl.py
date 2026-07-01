"""
ETL incremental: agrega SOLO los registros nuevos de crimes_220k (PocketBase) al
modelo estrella en MinIO, sin reconstruir todo.

Estrategia:
  1. Lee el fact consolidado (latest.parquet) → raw_row_id ya procesados + max(id).
  2. Extrae de PocketBase solo los registros cuyo id no está en el fact (los nuevos),
     recorriendo por @rowid descendente (los nuevos son los últimos insertados).
  3. Calcula los miembros NUEVOS de cada dimensión (continuando los ids existentes),
     los enriquece y los anexa a cada dimensión.
  4. Escribe hechos en lote append-only (sin reescribir el Parquet consolidado).
  5. Actualiza checkpoint + índice de IDs; parchea el total del dashboard (sin agregar todo el OLAP).

DuckDB lee consolidated/latest.parquet + fact_crimes/incremental/*.parquet.
"""

from __future__ import annotations

import io
import time
from typing import Any, Callable

import pandas as pd

from core.etl.fast_dim_lookup import load_dim_keys_cached, resolve_dim_for_batch
from core.etl.fast_keys import as_merge_str, composite_key
from core.etl.streaming_fact_writer import _build_fact_chunk
from core.etl.sync_checkpoint import (
    append_dim_delta,
    append_dim_keys_index,
    append_id_index,
    ensure_sync_state,
    patch_dashboard_fact_count,
    save_checkpoint,
    write_incremental_fact_batch,
)
from core.services.minio_store import DIM_COLLECTIONS, MinioParquetStore
from core.services.pocketbase import PocketBaseClient

ProgressFn = Callable[[dict[str, Any]], None]

# Tope por ejecución (carga incremental controlada desde la UI).
MAX_INCREMENTAL_BATCH = 300_000
MIN_INCREMENTAL_BATCH = 1

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
    return store.read_consolidated_fact_df()


def _write_consolidated_fact(store: MinioParquetStore, df: pd.DataFrame) -> None:
    """Solo para migraciones / consolidación manual (no usado en ruta rápida incremental)."""
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
    max_records: int | None = None,
    stop_streak: int = 2000,
    on_progress: ProgressFn | None = None,
) -> tuple[list[dict[str, Any]], int, int]:
    """
    Recorre crimes_220k por @rowid descendente (más recientes primero) con paginación.

    Solo acumula registros cuyo `id` NO está en MinIO (cero duplicados).
    Detiene cuando alcanza max_records nuevos o tras stop_streak existentes consecutivos.

    Returns:
        (nuevos, escaneados, omitidos_por_duplicado)
    """
    new_records: list[dict[str, Any]] = []
    consecutive_existing = 0
    scanned = 0
    skipped_duplicates = 0
    limit = max_records if max_records is not None else MAX_INCREMENTAL_BATCH

    for rec in pb.iter_records("crimes_220k", per_page=per_page, sort="-@rowid"):
        scanned += 1
        rid = str(rec.get("id", "")).strip()
        if not rid:
            continue
        if rid in existing_ids:
            skipped_duplicates += 1
            consecutive_existing += 1
            if consecutive_existing >= stop_streak:
                break
            continue
        consecutive_existing = 0
        new_records.append(rec)
        if len(new_records) >= limit:
            break
        if on_progress and len(new_records) % 1000 == 0:
            pct = min(40, 8 + int(32 * len(new_records) / max(limit, 1)))
            _emit(
                on_progress,
                phase="extract",
                percent=pct,
                message=(
                    f"Extraídos {len(new_records):,} nuevos "
                    f"(escaneados {scanned:,}, omitidos {skipped_duplicates:,})"
                ).replace(",", "."),
                new_count=len(new_records),
                scanned=scanned,
                skipped_duplicates=skipped_duplicates,
            )
    return new_records, scanned, skipped_duplicates


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
    cantidad_registros: int = MAX_INCREMENTAL_BATCH,
    per_page: int = 500,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    if cantidad_registros < MIN_INCREMENTAL_BATCH or cantidad_registros > MAX_INCREMENTAL_BATCH:
        raise ValueError(
            f"cantidad_registros debe estar entre {MIN_INCREMENTAL_BATCH} y {MAX_INCREMENTAL_BATCH}"
        )

    t0 = time.time()
    store = MinioParquetStore()
    fetch_page = min(max(cantidad_registros, 50), per_page)

    _emit(on_progress, phase="read", percent=2, message="Cargando checkpoint de sincronización...")
    existing_ids, max_fact_id, fact_count, dim_max_ids, checkpoint = ensure_sync_state(store)

    _emit(
        on_progress,
        phase="extract",
        percent=8,
        message=(
            f"Hechos en MinIO: {fact_count:,}. "
            f"Extrayendo hasta {cantidad_registros:,} nuevos desde PocketBase..."
        ).replace(",", "."),
    )

    with PocketBaseClient() as pb:
        pb.auth_admin()
        new_records, scanned, skipped_duplicates = _extract_new_records(
            pb,
            existing_ids,
            per_page=fetch_page,
            max_records=cantidad_registros,
            stop_streak=500 if cantidad_registros <= 500 else 2000,
            on_progress=on_progress,
        )

    if not new_records:
        return {
            "success": True,
            "new_records": 0,
            "cantidad_registros": cantidad_registros,
            "scanned": scanned,
            "skipped_duplicates": skipped_duplicates,
            "elapsed_seconds": round(time.time() - t0, 2),
            "message": "No hay registros nuevos en PocketBase respecto a MinIO. Nada que hacer.",
        }

    new_raw = _records_to_df(new_records)
    # Segunda barrera anti-duplicados antes de transformar (cero duplicados en el modelo).
    if "id" in new_raw.columns:
        before = len(new_raw)
        new_raw = new_raw[~new_raw["id"].astype(str).isin(existing_ids)].reset_index(drop=True)
        skipped_duplicates += before - len(new_raw)

    n_new = len(new_raw)
    if n_new == 0:
        return {
            "success": True,
            "new_records": 0,
            "cantidad_registros": cantidad_registros,
            "scanned": scanned,
            "skipped_duplicates": skipped_duplicates,
            "elapsed_seconds": round(time.time() - t0, 2),
            "message": "Todos los registros extraídos ya existían en MinIO (duplicados omitidos).",
        }

    _emit(
        on_progress,
        phase="transform",
        percent=45,
        message=f"{n_new:,} registros nuevos (sin duplicados). Calculando dimensiones...".replace(",", "."),
        new_count=n_new,
    )

    # Soporte de columnas geo opcionales (x/y) como en el pipeline completo.
    geo_cols = ["latitude", "longitude", "location"]
    for extra in ("x_coordinate", "y_coordinate"):
        if extra in new_raw.columns:
            geo_cols.append(extra)
    specs = dict(DIM_SPECS)
    specs["dim_ubicacion_geografica"] = (geo_cols, ["latitude", "longitude"], {})

    # Precarga índices compactos de dimensiones (una lectura S3 por dim; luego en RAM).
    for name in DIM_COLLECTIONS:
        _, key_cols, _ = specs[name]
        load_dim_keys_cached(store, name, key_cols)

    dims_for_fact: dict[str, pd.DataFrame] = {}
    dim_appends: dict[str, dict[str, Any]] = {}

    for name in DIM_COLLECTIONS:
        cols, key_cols, defaults = specs[name]
        lookup, enriched_new, total_dim = resolve_dim_for_batch(
            store,
            name,
            cols=cols,
            key_cols=key_cols,
            defaults=defaults,
            new_raw=new_raw,
            dim_max_ids=dim_max_ids,
        )
        dims_for_fact[name] = lookup
        if enriched_new.empty:
            dim_appends[name] = {"new": 0, "total": total_dim}
            continue
        append_dim_delta(store, name, enriched_new)
        cols, key_cols, _ = specs[name]
        append_dim_keys_index(store, name, enriched_new, key_cols)
        dim_appends[name] = {"new": len(enriched_new), "total": total_dim}
        _emit(
            on_progress,
            phase="upload",
            message=f"{name}: +{len(enriched_new):,} (total {total_dim:,})".replace(",", "."),
        )

    _emit(on_progress, phase="transform", percent=80, message="Construyendo hechos nuevos...")
    new_fact = _build_fact_chunk(new_raw, dims_for_fact, start_id=max_fact_id + 1)
    new_fact = new_fact.drop(columns=[c for c in new_fact.columns if c in ("year", "month")], errors="ignore")

    _emit(
        on_progress,
        phase="upload",
        percent=92,
        message=f"Guardando lote incremental de {len(new_fact):,} hechos...".replace(",", "."),
    )
    batch_key = write_incremental_fact_batch(store, new_fact)
    append_id_index(store, new_fact["raw_row_id"].astype(str).tolist())

    fact_after = fact_count + n_new
    max_fact_after = max_fact_id + n_new
    save_checkpoint(
        store,
        {
            **checkpoint,
            "max_fact_id": max_fact_after,
            "fact_count": fact_after,
            "dim_max_ids": dim_max_ids,
        },
    )
    store.invalidate_cache("fact_crimes")

    _emit(on_progress, phase="done", percent=98, message="Actualizando contador del dashboard...")
    patch_dashboard_fact_count(fact_after)

    elapsed = round(time.time() - t0, 2)
    return {
        "success": True,
        "new_records": n_new,
        "cantidad_registros": cantidad_registros,
        "scanned": scanned,
        "skipped_duplicates": skipped_duplicates,
        "fact_before": fact_count,
        "fact_after": fact_after,
        "dimensions": dim_appends,
        "elapsed_seconds": elapsed,
        "fast_path": True,
        "dashboard_deferred": True,
        "incremental_batch_key": batch_key,
        "message": (
            f"Carga incremental rápida: +{n_new} hechos en {elapsed}s "
            f"(total {fact_after:,}, límite {cantidad_registros:,}). "
            f"Dashboard: contador actualizado; agregaciones completas en segundo plano."
        ).replace(",", "."),
    }
