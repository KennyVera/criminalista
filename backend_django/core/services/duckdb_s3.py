"""
DuckDB + MinIO S3 (httpfs) — sesión compartida y consultas con proyección/filtro pushdown.
"""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import urlparse

import duckdb

from core.services.minio_store import MinioParquetStore


class DuckDBS3Session:
    """Conexión DuckDB in-process con httpfs apuntando a MinIO."""

    _shared: DuckDBS3Session | None = None

    def __init__(self, store: MinioParquetStore | None = None) -> None:
        self.store = store or MinioParquetStore()
        self._con: duckdb.DuckDBPyConnection | None = None

    @classmethod
    def shared(cls) -> DuckDBS3Session:
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    @classmethod
    def reset_shared(cls) -> None:
        if cls._shared is not None and cls._shared._con is not None:
            try:
                cls._shared._con.close()
            except Exception:
                pass
        cls._shared = None

    def s3_uri(self, key_or_glob: str) -> str:
        return f"s3://{self.store.bucket}/{key_or_glob}"

    def configure_s3(self, con: duckdb.DuckDBPyConnection) -> None:
        parsed = urlparse(self.store.endpoint)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 9000)
        use_ssl = parsed.scheme == "https"
        access = os.getenv("MINIO_ROOT_USER", "minioadmin")
        secret = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_change_me")

        con.execute("INSTALL httpfs;")
        con.execute("LOAD httpfs;")
        con.execute(f"SET s3_endpoint='{host}:{port}';")
        con.execute(f"SET s3_access_key_id='{access}';")
        con.execute(f"SET s3_secret_access_key='{secret}';")
        con.execute(f"SET s3_use_ssl={'true' if use_ssl else 'false'};")
        con.execute("SET s3_url_style='path';")
        con.execute("SET threads TO 4;")
        con.execute("SET enable_object_cache = true;")

    def connection(self) -> duckdb.DuckDBPyConnection:
        if self._con is None:
            self._con = duckdb.connect()
            self.configure_s3(self._con)
        return self._con

    def fact_parquet_source(self) -> str:
        prefix = self.store.prefix.rstrip("/")
        uris: list[str] = []
        if self.store.has_consolidated_facts():
            uris.append(self.s3_uri(self.store.fact_crimes_consolidated_key()))
            if self.store.has_incremental_facts():
                uris.append(self.s3_uri(f"{prefix}/fact_crimes/incremental/*.parquet"))
        elif self.store.has_partitioned_facts():
            uris.append(self.s3_uri(self.store.fact_crimes_glob()))
        else:
            uris.append(self.s3_uri(self.store._object_key("fact_crimes")))
        if len(uris) == 1:
            return uris[0]
        return "[" + ", ".join(f"'{u}'" for u in uris) + "]"

    def dim_parquet(self, collection: str) -> str:
        prefix = self.store.prefix.rstrip("/")
        base = self.s3_uri(self.store._object_key(collection))
        if self.store.has_dim_incremental(collection):
            delta = self.s3_uri(f"{prefix}/{collection}/incremental/*.parquet")
            return f"['{base}', '{delta}']"
        return base

    @staticmethod
    def read_parquet_expr(source: str) -> str:
        """Fragmento SQL listo para FROM read_parquet(...)."""
        if source.startswith("["):
            return f"read_parquet({source})"
        return f"read_parquet('{source}')"

    def _fact_read_sql(self) -> str:
        """hive_partitioning solo en hechos particionados (no en consolidado)."""
        fact = self.fact_parquet_source()
        if self.store.has_partitioned_facts() and not self.store.has_consolidated_facts():
            return f"read_parquet('{fact}', hive_partitioning = true)"
        return f"read_parquet('{fact}')"

    def execute(
        self,
        sql: str,
        *,
        params: list[Any] | None = None,
    ) -> duckdb.DuckDBPyRelation:
        con = self.connection()
        if params:
            return con.execute(sql, params)
        return con.execute(sql)

    def fetch_dicts(self, sql: str, *, params: list[Any] | None = None) -> list[dict[str, Any]]:
        rel = self.execute(sql, params=params)
        return rel.fetchdf().to_dict(orient="records")

    def filtered_crimes_aggregate(
        self,
        *,
        distrito: str | None = None,
        tipo: str | None = None,
        year: str | None = None,
        month: str | None = None,
        limit: int = 10_000,
    ) -> dict[str, Any]:
        """
        Agregación OLAP con joins mínimos y proyección de columnas.
        DuckDB descarga solo row-groups/columnas necesarios del Parquet en MinIO.
        """
        t0 = time.perf_counter()
        fact_read = self._fact_read_sql()
        dist = self.dim_parquet("dim_distrito_policial")
        tipo_dim = self.dim_parquet("dim_tipo_crimen")
        tiempo = self.dim_parquet("dim_tiempo")

        filters: list[str] = []
        if distrito:
            safe = str(distrito).replace("'", "''")
            filters.append(
                f"(CAST(d.district AS VARCHAR) = '{safe}' OR CAST(d.beat AS VARCHAR) = '{safe}')"
            )
        if tipo:
            safe = str(tipo).replace("'", "''")
            filters.append(f"CAST(t.primary_type AS VARCHAR) = '{safe}'")
        if year:
            safe = str(year).replace("'", "''")
            filters.append(f"CAST(ti.year AS VARCHAR) = '{safe}'")
        if month:
            safe = str(month).replace("'", "''")
            filters.append(f"CAST(ti.month AS VARCHAR) = '{safe}'")

        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        sql = f"""
            SELECT
                CAST(d.district AS VARCHAR) AS distrito,
                CAST(d.beat AS VARCHAR) AS beat,
                CAST(t.primary_type AS VARCHAR) AS tipo,
                CAST(ti.year AS VARCHAR) AS anio,
                CAST(ti.month AS VARCHAR) AS mes,
                COUNT(*)::BIGINT AS total
            FROM {fact_read} AS f
            INNER JOIN read_parquet('{dist}') AS d
                ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
            INNER JOIN read_parquet('{tipo_dim}') AS t
                ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(t.id AS BIGINT)
            INNER JOIN read_parquet('{tiempo}') AS ti
                ON CAST(f.fk_tiempo AS BIGINT) = CAST(ti.id AS BIGINT)
            {where}
            GROUP BY d.district, d.beat, t.primary_type, ti.year, ti.month
            ORDER BY total DESC
            LIMIT {int(limit)}
        """
        rows = self.fetch_dicts(sql)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        total = sum(int(r.get("total", 0) or 0) for r in rows)
        return {
            "rows": rows,
            "total_hechos": total,
            "query_ms": elapsed_ms,
            "source": "duckdb_s3_pushdown",
        }
