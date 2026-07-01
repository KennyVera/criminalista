"""
Estado liviano para ETL incremental rápido (sin leer/reescribir el fact completo).

- checkpoint.json: max_fact_id, fact_count
- synced_pb_ids.parquet: solo raw_row_id (deduplicación)
- fact_crimes/incremental/*.parquet: lotes append-only
"""

from __future__ import annotations

import io
import json
import uuid
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from django.core.cache import cache

from core.services.minio_store import MinioParquetStore

CHECKPOINT_VERSION = 1
PB_IDS_CACHE_KEY = "crimetrack:sync:pb_ids_v1"
PB_IDS_CACHE_TTL = 3600 * 6

# Eliminado: caché Redis del set completo (733k+ IDs es demasiado pesado).


def _sync_prefix(store: MinioParquetStore) -> str:
    return f"{store.prefix.rstrip('/')}/sync"


def checkpoint_key(store: MinioParquetStore) -> str:
    return f"{_sync_prefix(store)}/checkpoint.json"


def id_index_key(store: MinioParquetStore) -> str:
    return f"{_sync_prefix(store)}/synced_pb_ids.parquet"


def incremental_fact_prefix(store: MinioParquetStore) -> str:
    return f"{store.prefix.rstrip('/')}/fact_crimes/incremental/"


def load_checkpoint(store: MinioParquetStore) -> dict[str, Any] | None:
    try:
        obj = store._client.get_object(Bucket=store.bucket, Key=checkpoint_key(store))
        data = json.loads(obj["Body"].read().decode("utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_checkpoint(store: MinioParquetStore, data: dict[str, Any]) -> None:
    payload = {**data, "version": CHECKPOINT_VERSION}
    store._client.put_object(
        Bucket=store.bucket,
        Key=checkpoint_key(store),
        Body=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        ContentType="application/json",
    )


def has_incremental_facts(store: MinioParquetStore) -> bool:
    resp = store._client.list_objects_v2(
        Bucket=store.bucket,
        Prefix=incremental_fact_prefix(store),
        MaxKeys=1,
    )
    return bool(resp.get("Contents"))


def list_incremental_fact_keys(store: MinioParquetStore) -> list[str]:
    keys: list[str] = []
    paginator = store._client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=store.bucket, Prefix=incremental_fact_prefix(store)):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                keys.append(obj["Key"])
    return keys


def load_existing_ids(store: MinioParquetStore) -> set[str]:
    """Lee solo raw_row_id del índice Parquet (columna única, sin fact completo)."""
    from core.etl.fast_dim_lookup import cached_existing_ids

    def _load(store: MinioParquetStore) -> set[str]:
        key = id_index_key(store)
        try:
            obj = store._client.get_object(Bucket=store.bucket, Key=key)
            table = pq.read_table(io.BytesIO(obj["Body"].read()), columns=["raw_row_id"])
            col = table.column("raw_row_id").to_pylist()
            return {str(v).strip() for v in col if v is not None and str(v).strip()}
        except Exception:
            return set()

    return cached_existing_ids(store, _load)


def build_id_index_from_fact(store: MinioParquetStore, fact_df: pd.DataFrame) -> set[str]:
    if fact_df.empty or "raw_row_id" not in fact_df.columns:
        return set()
    ids = as_ids_series(fact_df["raw_row_id"])
    buffer = io.BytesIO()
    pq.write_table(pa.table({"raw_row_id": ids}), buffer, compression="snappy")
    buffer.seek(0)
    store._client.put_object(
        Bucket=store.bucket,
        Key=id_index_key(store),
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    cache.delete(PB_IDS_CACHE_KEY)
    from core.etl.fast_dim_lookup import invalidate_existing_ids_cache

    invalidate_existing_ids_cache()
    return set(ids.to_pylist())


def append_id_index(store: MinioParquetStore, new_ids: list[str]) -> None:
    if not new_ids:
        return
    cleaned = [str(i).strip() for i in new_ids if str(i).strip()]
    if not cleaned:
        return
    new_table = pa.table({"raw_row_id": cleaned})
    key = id_index_key(store)
    try:
        obj = store._client.get_object(Bucket=store.bucket, Key=key)
        existing = pq.read_table(io.BytesIO(obj["Body"].read()), columns=["raw_row_id"])
        combined = pa.concat_tables([existing, new_table])
    except Exception:
        combined = new_table
    buffer = io.BytesIO()
    pq.write_table(combined, buffer, compression="snappy")
    buffer.seek(0)
    store._client.put_object(
        Bucket=store.bucket,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    from core.etl.fast_dim_lookup import append_ids_to_process_cache

    append_ids_to_process_cache(cleaned)


def as_ids_series(series: pd.Series) -> pa.Array:
    return pa.array(series.astype(str).str.strip().tolist(), type=pa.string())


def dim_keys_index_key(store: MinioParquetStore, collection: str) -> str:
    return f"{_sync_prefix(store)}/dim_keys/{collection}.parquet"


def bootstrap_dim_key_indexes(store: MinioParquetStore) -> dict[str, int]:
    """Exporta key_cols+id livianos + max_id por dimensión."""
    from core.etl.incremental_etl import DIM_SPECS
    from core.services.minio_store import DIM_COLLECTIONS

    max_ids: dict[str, int] = {}
    for name in DIM_COLLECTIONS:
        _, key_cols, _ = DIM_SPECS[name]
        cols = list(dict.fromkeys([*key_cols, "id"]))
        df = store.read_parquet_columns(store._object_key(name), cols)
        if df.empty:
            max_ids[name] = 0
            continue
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, compression="snappy")
        buffer.seek(0)
        store._client.put_object(
            Bucket=store.bucket,
            Key=dim_keys_index_key(store, name),
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        max_ids[name] = int(pd.to_numeric(df["id"], errors="coerce").max())
    return max_ids


def append_dim_keys_index(store: MinioParquetStore, collection: str, enriched: pd.DataFrame, key_cols: list[str]) -> None:
    if enriched.empty:
        return
    cols = list(dict.fromkeys([*key_cols, "id"]))
    slice_df = enriched[cols].copy()
    key = dim_keys_index_key(store, collection)
    try:
        obj = store._client.get_object(Bucket=store.bucket, Key=key)
        existing = pd.read_parquet(io.BytesIO(obj["Body"].read()))
        combined = pd.concat([existing, slice_df], ignore_index=True)
    except Exception:
        combined = slice_df
    buffer = io.BytesIO()
    combined.to_parquet(buffer, index=False, compression="snappy")
    buffer.seek(0)
    store._client.put_object(
        Bucket=store.bucket,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )


def dim_keys_ready(store: MinioParquetStore) -> bool:
    try:
        store._client.head_object(
            Bucket=store.bucket,
            Key=dim_keys_index_key(store, "dim_caso"),
        )
        return True
    except Exception:
        return False


def ensure_dim_keys_indexes(store: MinioParquetStore, dim_max_ids: dict[str, int] | None = None) -> dict[str, int]:
    if dim_keys_ready(store) and dim_max_ids:
        return dim_max_ids
    return bootstrap_dim_key_indexes(store)
def bootstrap_dim_max_ids(store: MinioParquetStore) -> dict[str, int]:
    checkpoint = load_checkpoint(store)
    if checkpoint and checkpoint.get("dim_max_ids") and dim_keys_ready(store):
        return {k: int(v) for k, v in checkpoint["dim_max_ids"].items()}
    return bootstrap_dim_key_indexes(store)


def get_dim_max_ids(store: MinioParquetStore, checkpoint: dict[str, Any] | None) -> dict[str, int]:
    if checkpoint and checkpoint.get("dim_max_ids"):
        return {k: int(v) for k, v in checkpoint["dim_max_ids"].items()}
    return bootstrap_dim_max_ids(store)


def ensure_sync_state(
    store: MinioParquetStore,
    fact_df: pd.DataFrame | None = None,
) -> tuple[set[str], int, int, dict[str, int], dict[str, Any]]:
    """
    Returns:
        (existing_ids, max_fact_id, fact_count, dim_max_ids, checkpoint)
    """
    checkpoint = load_checkpoint(store) or {}
    existing_ids = load_existing_ids(store)

    if checkpoint and existing_ids and checkpoint.get("max_fact_id") is not None:
        dim_max_ids = ensure_dim_keys_indexes(store, get_dim_max_ids(store, checkpoint))
        checkpoint["dim_max_ids"] = dim_max_ids
        save_checkpoint(store, checkpoint)
        return (
            existing_ids,
            int(checkpoint["max_fact_id"]),
            int(checkpoint.get("fact_count", len(existing_ids))),
            dim_max_ids,
            checkpoint,
        )

    if fact_df is None:
        fact_df = store.read_consolidated_fact_df()

    if fact_df.empty:
        raise ValueError("No hay fact consolidado para inicializar checkpoint.")

    if not existing_ids:
        existing_ids = build_id_index_from_fact(store, fact_df)

    max_fact_id = int(pd.to_numeric(fact_df["id"], errors="coerce").max())
    fact_count = len(fact_df)
    dim_max_ids = bootstrap_dim_key_indexes(store)
    checkpoint = {
        "max_fact_id": max_fact_id,
        "fact_count": fact_count,
        "dim_max_ids": dim_max_ids,
    }
    save_checkpoint(store, checkpoint)
    return existing_ids, max_fact_id, fact_count, dim_max_ids, checkpoint


def write_incremental_fact_batch(store: MinioParquetStore, fact_df: pd.DataFrame) -> str:
    batch_key = f"{incremental_fact_prefix(store)}batch_{uuid.uuid4().hex}.parquet"
    buffer = io.BytesIO()
    fact_df.to_parquet(buffer, index=False, compression="snappy")
    buffer.seek(0)
    store._client.put_object(
        Bucket=store.bucket,
        Key=batch_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    return batch_key


def incremental_dim_prefix(store: MinioParquetStore, collection: str) -> str:
    return f"{store.prefix.rstrip('/')}/{collection}/incremental/"


def list_incremental_dim_keys(store: MinioParquetStore, collection: str) -> list[str]:
    keys: list[str] = []
    prefix = incremental_dim_prefix(store, collection)
    paginator = store._client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=store.bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                keys.append(obj["Key"])
    return keys


def append_dim_delta(store: MinioParquetStore, collection: str, df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    batch_key = f"{incremental_dim_prefix(store, collection)}batch_{uuid.uuid4().hex}.parquet"
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, compression="snappy")
    buffer.seek(0)
    store._client.put_object(
        Bucket=store.bucket,
        Key=batch_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    store.invalidate_cache(collection)
    return batch_key


def read_dim_with_deltas(
    store: MinioParquetStore,
    collection: str,
    columns: list[str],
) -> pd.DataFrame:
    """Lee dimensión base + lotes incrementales (solo columnas pedidas)."""
    base = store.read_parquet_columns(store._object_key(collection), columns)
    frames = [base] if not base.empty else []
    for key in list_incremental_dim_keys(store, collection):
        delta = store.read_parquet_columns(key, columns)
        if not delta.empty:
            frames.append(delta)
    if not frames:
        return pd.DataFrame(columns=columns)
    combined = pd.concat(frames, ignore_index=True)
    return combined


def clear_incremental_state(store: MinioParquetStore) -> None:
    """Usar tras reconstrucción completa."""
    store.delete_prefix(incremental_fact_prefix(store))
    for collection in (
        "dim_actualizacion",
        "dim_area_administrativa",
        "dim_arresto",
        "dim_caso",
        "dim_distrito_policial",
        "dim_tiempo",
        "dim_tipo_crimen",
        "dim_ubicacion_geografica",
        "dim_ubicacion_lugar",
        "dim_violencia_domestica",
    ):
        store.delete_prefix(incremental_dim_prefix(store, collection))
    for key in (checkpoint_key(store), id_index_key(store)):
        try:
            store._client.delete_object(Bucket=store.bucket, Key=key)
        except Exception:
            pass
    store.delete_prefix(f"{_sync_prefix(store)}/dim_keys/")


def patch_dashboard_fact_count(fact_count: int) -> None:
    """Actualiza solo el total en el resumen (ms), sin re-agregar todo el OLAP."""
    from packages.dashboard_analitica.services.dashboard_summary_store import DashboardSummaryStore

    summary = DashboardSummaryStore()
    overview = summary.get_payload("overview")
    if isinstance(overview, dict):
        patched = dict(overview)
        totals = dict(patched.get("totals") or {})
        totals["crimes_220k"] = fact_count
        totals["source"] = "minio_olap"
        patched["totals"] = totals
        patched["incremental_pending_refresh"] = True
        summary.upsert_payload("overview", patched)
