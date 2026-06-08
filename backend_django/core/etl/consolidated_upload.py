"""
Carga consolidada de fact_crimes: un único Parquet por ejecución ETL (sin miles de particiones).
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore

CONSOLIDATED_DIR = "consolidated"
LATEST_KEY = "latest.parquet"


def consolidated_object_key(store: MinioParquetStore, *, run_id: str | None = None) -> str:
    prefix = store.prefix.rstrip("/")
    if run_id:
        return f"{prefix}/fact_crimes/{CONSOLIDATED_DIR}/run_{run_id}.parquet"
    return f"{prefix}/fact_crimes/{CONSOLIDATED_DIR}/{LATEST_KEY}"


def has_consolidated_facts(store: MinioParquetStore | None = None) -> bool:
    store = store or MinioParquetStore()
    key = consolidated_object_key(store)
    try:
        store._client.head_object(Bucket=store.bucket, Key=key)
        return True
    except Exception:
        return False


def write_consolidated_fact_crimes(
    store: MinioParquetStore,
    fact_df: pd.DataFrame,
    dims: dict[str, pd.DataFrame],
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Escribe un solo Parquet con todos los hechos.
    Elimina particiones Hive previas para evitar duplicar lecturas.
    """
    del dims  # reservado; year/month no se usan en layout consolidado

    if fact_df.empty:
        return {"rows": 0, "paths": [], "layout": "consolidated"}

    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    latest_key = consolidated_object_key(store)
    snapshot_key = consolidated_object_key(store, run_id=run_id)

    partition_prefix = f"{store.prefix.rstrip('/')}/fact_crimes/"
    store.delete_prefix(partition_prefix)

    legacy = store._object_key("fact_crimes")
    try:
        store._client.delete_object(Bucket=store.bucket, Key=legacy)
    except Exception:
        pass

    out_df = fact_df.drop(columns=[c for c in fact_df.columns if c in ("year", "month")], errors="ignore")

    def _put(key: str) -> None:
        buffer = io.BytesIO()
        out_df.to_parquet(buffer, index=False, compression="snappy")
        buffer.seek(0)
        store._client.put_object(
            Bucket=store.bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )

    _put(latest_key)
    _put(snapshot_key)
    store.invalidate_cache("fact_crimes")

    return {
        "rows": len(out_df),
        "paths": [latest_key, snapshot_key],
        "layout": "consolidated",
        "run_id": run_id,
        "message": f"fact_crimes consolidado ({len(out_df):,} filas, 1 Parquet).".replace(",", "."),
    }
