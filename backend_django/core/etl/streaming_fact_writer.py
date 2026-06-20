"""
Escritura de fact_crimes vía DuckDB staging — COPY directo a MinIO sin DataFrame monolítico.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from typing import Any

import duckdb
import pandas as pd

from core.etl.consolidated_upload import consolidated_object_key
from core.etl.fast_keys import as_merge_str, map_foreign_key
from core.services.duckdb_s3 import DuckDBS3Session
from core.services.minio_store import MinioParquetStore

FACT_COLUMNS = [
    "id",
    "raw_row_id",
    "fk_caso",
    "fk_tipo_crimen",
    "fk_distrito",
    "fk_area",
    "fk_tiempo",
    "fk_ubicacion_lugar",
    "fk_ubicacion_geo",
    "fk_arresto",
    "fk_domestico",
    "fk_actualizacion",
]


def _build_fact_chunk(
    raw_df: pd.DataFrame,
    dims: dict[str, pd.DataFrame],
    *,
    start_id: int,
) -> pd.DataFrame:
    """Construye hechos de un chunk con IDs globales continuos."""
    if raw_df.empty:
        return pd.DataFrame(columns=FACT_COLUMNS)

    raw = raw_df.drop(columns=[c for c in raw_df.columns if c.startswith("fk_")], errors="ignore")
    n = len(raw)
    fact = pd.DataFrame(
        {
            "id": pd.Series(range(start_id, start_id + n), dtype="int64"),
            "raw_row_id": as_merge_str(raw.get("id", pd.Series(range(start_id, start_id + n)))),
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


class DuckDBFactStreamWriter:
    """
    Inserta hechos chunk a chunk en DuckDB (disco) y sube a MinIO con COPY ... TO s3://
    """

    def __init__(self) -> None:
        self._tmp_path = os.path.join(
            tempfile.gettempdir(),
            f"crimetrack_etl_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.duckdb",
        )
        self._con = duckdb.connect(self._tmp_path)
        self._next_id = 1
        self._row_count = 0
        self._configure_writer()
        self._create_staging()

    def _configure_writer(self) -> None:
        mem_limit = os.getenv("ETL_DUCKDB_MEMORY_LIMIT", "1GB")
        self._con.execute(f"SET memory_limit='{mem_limit}';")
        self._con.execute("SET preserve_insertion_order=false;")

    def _create_staging(self) -> None:
        self._con.execute(
            """
            CREATE TABLE fact_staging (
                id BIGINT,
                raw_row_id VARCHAR,
                fk_caso BIGINT,
                fk_tipo_crimen BIGINT,
                fk_distrito BIGINT,
                fk_area BIGINT,
                fk_tiempo BIGINT,
                fk_ubicacion_lugar BIGINT,
                fk_ubicacion_geo BIGINT,
                fk_arresto BIGINT,
                fk_domestico BIGINT,
                fk_actualizacion BIGINT
            );
            """
        )

    def append_chunk(self, raw_df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> int:
        fact = _build_fact_chunk(raw_df, dims, start_id=self._next_id)
        if fact.empty:
            return 0
        self._con.register("_fact_chunk", fact)
        self._con.execute("INSERT INTO fact_staging SELECT * FROM _fact_chunk")
        self._con.unregister("_fact_chunk")

        n = len(fact)
        self._next_id += n
        self._row_count += n
        del fact
        return n

    @property
    def row_count(self) -> int:
        return self._row_count

    def flush_to_minio(
        self,
        store: MinioParquetStore,
        *,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        if self._row_count == 0:
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

        duck = DuckDBS3Session(store)
        duck.configure_s3(self._con)

        self._con.execute(
            f"""
            COPY (
                SELECT
                    id,
                    raw_row_id,
                    fk_caso,
                    fk_tipo_crimen,
                    fk_distrito,
                    fk_area,
                    fk_tiempo,
                    fk_ubicacion_lugar,
                    fk_ubicacion_geo,
                    fk_arresto,
                    fk_domestico,
                    fk_actualizacion
                FROM fact_staging
            ) TO '{duck.s3_uri(latest_key)}'
            (FORMAT PARQUET, COMPRESSION SNAPPY, OVERWRITE TRUE);
            """
        )
        self._con.execute(
            f"""
            COPY (
                SELECT
                    id,
                    raw_row_id,
                    fk_caso,
                    fk_tipo_crimen,
                    fk_distrito,
                    fk_area,
                    fk_tiempo,
                    fk_ubicacion_lugar,
                    fk_ubicacion_geo,
                    fk_arresto,
                    fk_domestico,
                    fk_actualizacion
                FROM fact_staging
            ) TO '{duck.s3_uri(snapshot_key)}'
            (FORMAT PARQUET, COMPRESSION SNAPPY, OVERWRITE TRUE);
            """
        )

        store.invalidate_cache("fact_crimes")
        return {
            "rows": self._row_count,
            "paths": [latest_key, snapshot_key],
            "layout": "consolidated",
            "run_id": run_id,
            "writer": "duckdb_copy_s3",
            "message": (
                f"fact_crimes consolidado ({self._row_count:,} filas, streaming DuckDB→S3)."
            ).replace(",", "."),
        }

    def close(self) -> None:
        try:
            self._con.close()
        except Exception:
            pass
        try:
            if os.path.exists(self._tmp_path):
                os.remove(self._tmp_path)
        except OSError:
            pass

    def __enter__(self) -> DuckDBFactStreamWriter:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
