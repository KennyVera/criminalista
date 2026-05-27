"""
Escritura particionada Hive (year/month) de fact_crimes en MinIO.
"""

from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore

UPLOAD_WORKERS = 8


def attach_year_month_to_fact(fact_df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Añade columnas de particion desde dim_tiempo (mapeo vectorizado)."""
    fact = fact_df.copy()
    tiempo = dims.get("dim_tiempo", pd.DataFrame())
    if tiempo.empty or "fk_tiempo" not in fact.columns:
        fact["year"] = 0
        fact["month"] = 1
        return fact

    ym = tiempo[["id", "year", "month"]].copy()
    ym = ym.set_index(pd.to_numeric(ym["id"], errors="coerce"))
    fk = pd.to_numeric(fact["fk_tiempo"], errors="coerce")
    fact["year"] = fk.map(ym["year"]).fillna(0)
    fact["month"] = fk.map(ym["month"]).fillna(1)
    fact["year"] = pd.to_numeric(fact["year"], errors="coerce").fillna(0).astype(int)
    fact["month"] = pd.to_numeric(fact["month"], errors="coerce").fillna(1).astype(int)
    fact["month"] = fact["month"].clip(1, 12)
    return fact


def _upload_partition(
    store: MinioParquetStore,
    year: int,
    month: int,
    group: pd.DataFrame,
) -> tuple[str, int]:
    partition_key = f"{store.prefix}/fact_crimes/year={year}/month={month:02d}/data.parquet"
    buffer = io.BytesIO()
    group.drop(columns=["year", "month"], errors="ignore").to_parquet(
        buffer, index=False, compression="snappy"
    )
    buffer.seek(0)
    store._client.put_object(
        Bucket=store.bucket,
        Key=partition_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    return partition_key, len(group)


def write_partitioned_fact_crimes(
    store: MinioParquetStore,
    fact_df: pd.DataFrame,
    dims: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """
    Sube fact_crimes como:
      datasets/star/fact_crimes/year=YYYY/month=MM/data.parquet
    """
    if fact_df.empty:
        return {"partitions": 0, "rows": 0, "paths": []}

    fact = attach_year_month_to_fact(fact_df, dims)

    legacy_key = store._object_key("fact_crimes")
    store.delete_prefix(f"{store.prefix}/fact_crimes/")
    try:
        store._client.delete_object(Bucket=store.bucket, Key=legacy_key)
    except Exception:
        pass

    groups = [(int(y), int(m), grp) for (y, m), grp in fact.groupby(["year", "month"], sort=True)]
    paths: list[str] = []
    rows_written = 0

    workers = min(UPLOAD_WORKERS, max(1, len(groups)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_upload_partition, store, y, m, grp) for y, m, grp in groups
        ]
        for fut in as_completed(futures):
            path, n = fut.result()
            paths.append(path)
            rows_written += n

    store.invalidate_cache("fact_crimes")
    return {
        "partitions": len(groups),
        "rows": rows_written,
        "paths": sorted(paths)[:20],
        "layout": "hive/year/month",
    }
