"""
ETL: crimes_220k (PocketBase) → modelo estrella Parquet → MinIO.

Pipeline streaming (memoria plana en Celery):
  1. Extraer por chunks (skipTotal=1)
  2. Dimensiones incrementales chunk a chunk
  3. Hechos en DuckDB staging → COPY Snappy directo a MinIO
"""

from __future__ import annotations

import gc
import io
import os
import time
from typing import Any, Callable

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from core.etl.dim_enrichment import enrich_all_dimensions
from core.etl.incremental_dims import IncrementalDimStore
from core.etl.pb_fetch import FETCH_PER_PAGE, iter_crimes_220k_chunks
from core.etl.streaming_fact_writer import DuckDBFactStreamWriter
from core.services.minio_store import DIM_COLLECTIONS, MinioParquetStore
from core.services.pocketbase import PocketBaseClient

ProgressFn = Callable[[dict[str, Any]], None]

_PB_DROP_COLS = frozenset({"collectionId", "collectionName", "expand"})


def _emit(on_progress: ProgressFn | None, **kwargs: Any) -> None:
    if on_progress:
        on_progress(kwargs)


def _chunk_to_dataframe(chunk: list[dict[str, Any]]) -> pd.DataFrame:
    if not chunk:
        return pd.DataFrame()
    df = pd.DataFrame(chunk)
    return df.drop(columns=[c for c in df.columns if c in _PB_DROP_COLS], errors="ignore")


def _should_skip_raw_export(row_count: int, export_raw_copy: bool) -> bool:
    if not export_raw_copy:
        return True
    if os.getenv("ETL_SKIP_RAW_EXPORT", "").lower() in ("1", "true", "yes"):
        return True
    return row_count > int(os.getenv("ETL_RAW_EXPORT_MAX_ROWS", "50000"))


class _RawParquetStream:
    """Acumula chunks raw en un Parquet Snappy en buffer durante el mismo recorrido PB."""

    def __init__(self) -> None:
        self._buffer = io.BytesIO()
        self._writer: pq.ParquetWriter | None = None
        self.total = 0

    def write_chunk(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        table = pa.Table.from_pandas(df, preserve_index=False)
        if self._writer is None:
            self._writer = pq.ParquetWriter(self._buffer, table.schema, compression="snappy")
        self._writer.write_table(table)
        self.total += len(df)

    def flush_to_minio(self, store: MinioParquetStore) -> int:
        if self._writer is None:
            return 0
        self._writer.close()
        self._buffer.seek(0)
        store._client.put_object(
            Bucket=store.bucket,
            Key=store._object_key("crimes_220k"),
            Body=self._buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        store.invalidate_cache("crimes_220k")
        return self.total


def run_etl_pb_to_minio(
    *,
    export_raw_copy: bool = True,
    on_progress: ProgressFn | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """
    Pipeline ETL streaming:
      1. PocketBase → chunks (skipTotal=1)
      2. Dimensiones incrementales + hechos en DuckDB (disco)
      3. COPY Parquet Snappy → MinIO (sin DataFrame monolítico en RAM)
    """

    def _abort_if_cancelled() -> None:
        if should_cancel and should_cancel():
            raise RuntimeError("ETL cancelado por el usuario.")

    from core.etl.sync_checkpoint import clear_incremental_state

    store = MinioParquetStore()
    clear_incremental_state(store)

    t0 = time.time()
    per_page = int(os.getenv("ETL_PB_PER_PAGE", str(FETCH_PER_PAGE)))
    dim_store = IncrementalDimStore()
    total_raw = 0
    page = 0

    _abort_if_cancelled()
    _emit(on_progress, phase="extract", percent=5, message="Extrayendo crimes_220k (streaming)...")

    store = MinioParquetStore()
    summary: dict[str, Any] = {"collections": {}, "pipeline": "streaming"}
    raw_stream: _RawParquetStream | None = None
    if export_raw_copy and os.getenv("ETL_SKIP_RAW_EXPORT", "").lower() not in (
        "1",
        "true",
        "yes",
    ):
        raw_stream = _RawParquetStream()

    with PocketBaseClient() as pb:
        pb.auth_admin()

        with DuckDBFactStreamWriter() as fact_writer:
            for chunk in iter_crimes_220k_chunks(pb, per_page=per_page):
                _abort_if_cancelled()
                page += 1
                chunk_df = _chunk_to_dataframe(chunk)
                if chunk_df.empty:
                    continue

                if raw_stream is not None:
                    raw_stream.write_chunk(chunk_df)

                dim_store.ingest_chunk(chunk_df)
                dims_partial = dim_store.to_dataframes()
                inserted = fact_writer.append_chunk(chunk_df, dims_partial)

                total_raw += len(chunk_df)
                del chunk_df, dims_partial, chunk

                pct = min(55, 5 + int(page * 0.5))
                _emit(
                    on_progress,
                    phase="transform",
                    percent=pct,
                    message=(
                        f"Chunk {page}: {total_raw:,} filas · +{inserted} hechos staging"
                    ).replace(",", "."),
                    raw_rows=total_raw,
                    dim_keys=dim_store.total_rows,
                )

                if page % 10 == 0:
                    gc.collect()

            if total_raw == 0:
                raise ValueError(
                    "No hay registros en crimes_220k (PocketBase). "
                    "Ejecuta migrate_from_postgres --steps raw primero."
                )

            _emit(
                on_progress,
                phase="transform",
                percent=56,
                message="Enriqueciendo dimensiones...",
                raw_rows=total_raw,
            )
            dims = enrich_all_dimensions(dim_store.to_dataframes())

            _emit(on_progress, phase="upload", percent=60, message="Subiendo dimensiones a MinIO...")
            for i, name in enumerate(DIM_COLLECTIONS):
                _abort_if_cancelled()
                store.write_df(name, dims[name])
                summary["collections"][name] = len(dims[name])
                pct = 60 + int(15 * (i + 1) / len(DIM_COLLECTIONS))
                _emit(on_progress, phase="upload", percent=pct, message=f"Dimension {name} lista.")

            if raw_stream is not None:
                if total_raw <= int(os.getenv("ETL_RAW_EXPORT_MAX_ROWS", "50000")):
                    _emit(
                        on_progress,
                        phase="upload",
                        percent=76,
                        message="Subiendo raw crimes_220k...",
                    )
                    summary["collections"]["crimes_220k"] = raw_stream.flush_to_minio(store)
                else:
                    summary["raw_export_skipped"] = True
                    summary["raw_export_reason"] = "ETL_RAW_EXPORT_MAX_ROWS"
            else:
                summary["raw_export_skipped"] = True

            _abort_if_cancelled()
            _emit(
                on_progress,
                phase="upload",
                percent=85,
                message="COPY fact_crimes DuckDB → MinIO (Snappy)...",
            )
            consolidated_meta = fact_writer.flush_to_minio(store)

    summary["raw_rows"] = total_raw
    summary["collections"]["fact_crimes"] = consolidated_meta["rows"]
    summary["fact_consolidated"] = consolidated_meta
    summary["elapsed_seconds"] = round(time.time() - t0, 2)

    _emit(on_progress, phase="done", percent=100, message="ETL completado.")

    from packages.dashboard_analitica.services.summary_materializer import (
        materialize_dashboard_summary,
    )

    materialize_dashboard_summary()

    return {
        "success": True,
        "message": (
            f"ETL streaming en {summary['elapsed_seconds']}s: {total_raw} filas crudas → "
            f"{consolidated_meta['rows']} hechos (DuckDB→S3) y "
            f"{len(DIM_COLLECTIONS)} dimensiones en MinIO."
        ),
        **summary,
    }
