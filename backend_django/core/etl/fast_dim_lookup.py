"""Lookup de dimensiones por lote (DuckDB) sin cargar Parquets completos en RAM."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.etl.fast_keys import as_merge_str, composite_key
from core.etl.sync_checkpoint import dim_keys_index_key
from core.services.analytics_service import AnalyticsService
from core.services.duckdb_s3 import DuckDBS3Session
from core.services.minio_store import MinioParquetStore

_PROCESS_ID_CACHE: dict[str, set[str]] = {}


def cached_existing_ids(store: MinioParquetStore, loader) -> set[str]:
    key = loader.__name__
    if key not in _PROCESS_ID_CACHE:
        _PROCESS_ID_CACHE[key] = loader(store)
    return _PROCESS_ID_CACHE[key]


def append_ids_to_process_cache(new_ids: list[str]) -> None:
    cleaned = {str(i).strip() for i in new_ids if str(i).strip()}
    if not cleaned:
        return
    for ids in _PROCESS_ID_CACHE.values():
        ids.update(cleaned)


def invalidate_existing_ids_cache() -> None:
    _PROCESS_ID_CACHE.clear()


def invalidate_all_sync_caches() -> None:
    invalidate_existing_ids_cache()
    invalidate_dim_keys_cache()


def dim_max_id_scan(store: MinioParquetStore, collection: str) -> int:
    an = AnalyticsService(store)
    con = an.connection()
    src = an._dim_parquet(collection)
    expr = DuckDBS3Session.read_parquet_expr(src)
    row = con.execute(
        f"SELECT COALESCE(MAX(CAST(id AS BIGINT)), 0) FROM {expr}"
    ).fetchone()
    return int(row[0]) if row else 0


_DIM_KEYS_CACHE: dict[str, pd.DataFrame] = {}


def _dim_keys_cache_key(store: MinioParquetStore, collection: str) -> str:
    return dim_keys_index_key(store, collection)


def load_dim_keys_cached(store: MinioParquetStore, collection: str, key_cols: list[str]) -> pd.DataFrame:
    cache_key = _dim_keys_cache_key(store, collection)
    if cache_key in _DIM_KEYS_CACHE:
        return _DIM_KEYS_CACHE[cache_key]
    cols = list(dict.fromkeys([*key_cols, "id"]))
    df = store.read_parquet_columns(cache_key, cols)
    for col in key_cols:
        if col in df.columns:
            df[col] = as_merge_str(df[col])
    _DIM_KEYS_CACHE[cache_key] = df
    return df


def invalidate_dim_keys_cache() -> None:
    _DIM_KEYS_CACHE.clear()


def lookup_dim_keys(
    store: MinioParquetStore,
    collection: str,
    key_cols: list[str],
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Devuelve key_cols + id para claves del lote que ya existen en la dimensión."""
    if candidates.empty or not all(k in candidates.columns for k in key_cols):
        return pd.DataFrame(columns=[*key_cols, "id"])

    dim_df = load_dim_keys_cached(store, collection, key_cols)
    if dim_df.empty:
        return pd.DataFrame(columns=[*key_cols, "id"])

    work = candidates[key_cols].copy()
    for col in key_cols:
        work[col] = as_merge_str(work[col])
    work = work.drop_duplicates(subset=key_cols, keep="first").reset_index(drop=True)

    left_key = composite_key(work, key_cols)
    right_key = composite_key(dim_df, key_cols)
    id_map = pd.Series(dim_df["id"].values, index=right_key.values)
    id_map = id_map[~id_map.index.duplicated(keep="first")]
    matched = work.copy()
    matched["id"] = left_key.map(id_map)
    matched = matched.dropna(subset=["id"])
    matched["id"] = pd.to_numeric(matched["id"], errors="coerce").astype("Int64")
    return matched


def resolve_dim_for_batch(
    store: MinioParquetStore,
    collection: str,
    *,
    cols: list[str],
    key_cols: list[str],
    defaults: dict[str, Any],
    new_raw: pd.DataFrame,
    dim_max_ids: dict[str, int],
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """
    Returns:
        (dim_lookup_for_fk, new_members_enriched, total_dim_estimate)
    """
    from core.etl.dim_enrichment import ENRICHERS, _add_legacy_id

    cols_present = [c for c in cols if c in new_raw.columns]
    if not all(k in cols_present for k in key_cols):
        empty = pd.DataFrame(columns=[*key_cols, "id"])
        current = int(dim_max_ids.get(collection, 0))
        return empty, empty, current

    subset = new_raw[cols_present].copy()
    for col in subset.columns:
        subset[col] = as_merge_str(subset[col])
    subset = subset.drop_duplicates(subset=key_cols, keep="first").reset_index(drop=True)

    matched = lookup_dim_keys(store, collection, key_cols, subset)
    if matched.empty:
        keys_matched = pd.Series(dtype=str)
    else:
        keys_matched = composite_key(matched, key_cols)

    all_keys = composite_key(subset, key_cols)
    missing_mask = ~all_keys.isin(set(keys_matched.tolist()))
    new_members = subset.loc[missing_mask].reset_index(drop=True)

    if new_members.empty:
        total = int(dim_max_ids.get(collection, 0))
        return matched[key_cols + ["id"]], pd.DataFrame(), total

    max_id = int(dim_max_ids.get(collection, 0))
    new_members.insert(0, "id", range(max_id + 1, max_id + 1 + len(new_members)))
    for k, v in defaults.items():
        new_members[k] = v

    enricher = ENRICHERS.get(collection)
    enriched = enricher(new_members) if enricher else _add_legacy_id(new_members)
    lookup = pd.concat([matched[key_cols + ["id"]], enriched[key_cols + ["id"]]], ignore_index=True)
    total = max_id + len(new_members)
    dim_max_ids[collection] = total
    # Mantener caché en memoria al día (evita releer MinIO en el siguiente lote).
    cache_key = _dim_keys_cache_key(store, collection)
    if cache_key in _DIM_KEYS_CACHE and not enriched.empty:
        slice_df = enriched[[*key_cols, "id"]].copy()
        for col in key_cols:
            slice_df[col] = as_merge_str(slice_df[col])
        _DIM_KEYS_CACHE[cache_key] = pd.concat([_DIM_KEYS_CACHE[cache_key], slice_df], ignore_index=True)
    return lookup, enriched, total
