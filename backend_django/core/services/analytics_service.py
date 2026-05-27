"""
Consultas analiticas ultrarrapidas: DuckDB lee Parquet en MinIO via S3 (sin cargar todo en RAM).
"""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import urlparse

import duckdb

from core.collections_meta import COLLECTIONS
from core.services.minio_store import DIM_COLLECTIONS, MinioParquetStore
from core.services.pocketbase import PocketBaseClient

DASHBOARD_CACHE_KEY = "crimetrack:dashboard:stats:v3"
DASHBOARD_CACHE_TTL = 60 * 15  # 15 minutos


class AnalyticsService:
    def __init__(self, store: MinioParquetStore | None = None):
        self.store = store or MinioParquetStore()
        self._con: duckdb.DuckDBPyConnection | None = None

    def _s3_uri(self, key_or_glob: str) -> str:
        return f"s3://{self.store.bucket}/{key_or_glob}"

    def _configure_s3(self, con: duckdb.DuckDBPyConnection) -> None:
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

    def connection(self) -> duckdb.DuckDBPyConnection:
        if self._con is None:
            self._con = duckdb.connect()
            self._configure_s3(self._con)
        return self._con

    def _fact_parquet_source(self) -> str:
        if self.store.has_partitioned_facts():
            return self._s3_uri(self.store.fact_crimes_glob())
        return self._s3_uri(self.store._object_key("fact_crimes"))

    def _dim_parquet(self, collection: str) -> str:
        return self._s3_uri(self.store._object_key(collection))

    def count_fact_crimes(self) -> int:
        con = self.connection()
        src = self._fact_parquet_source()
        row = con.execute(f"SELECT COUNT(*)::BIGINT AS c FROM read_parquet('{src}')").fetchone()
        return int(row[0]) if row else 0

    def count_dimension(self, collection: str) -> int:
        con = self.connection()
        src = self._dim_parquet(collection)
        try:
            row = con.execute(f"SELECT COUNT(*)::BIGINT FROM read_parquet('{src}')").fetchone()
            return int(row[0]) if row else 0
        except Exception:
            return self.store.count(collection)

    def crimes_by_district(self, *, limit: int = 25) -> list[dict[str, Any]]:
        """
        Ejemplo agregacion SQL: conteo de crimenes por distrito (usa particiones year/month).
        """
        con = self.connection()
        fact = self._fact_parquet_source()
        dist = self._dim_parquet("dim_distrito_policial")
        sql = f"""
            SELECT
                CAST(d.district AS VARCHAR) AS district,
                CAST(d.beat AS VARCHAR) AS beat,
                COUNT(*)::BIGINT AS total_crimes
            FROM read_parquet('{fact}') AS f
            INNER JOIN read_parquet('{dist}') AS d
                ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
            GROUP BY d.district, d.beat
            ORDER BY total_crimes DESC
            LIMIT {int(limit)}
        """
        t0 = time.perf_counter()
        rows = con.execute(sql).fetchdf()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        items = rows.to_dict(orient="records")
        return {"items": items, "query_ms": elapsed_ms, "source": "duckdb+s3"}

    def recent_facts(self, *, limit: int = 8) -> list[dict]:
        con = self.connection()
        fact = self._fact_parquet_source()
        tipo = self._dim_parquet("dim_tipo_crimen")
        dist = self._dim_parquet("dim_distrito_policial")
        tiempo = self._dim_parquet("dim_tiempo")
        sql = f"""
            SELECT
                f.id,
                f.raw_row_id AS legacy_id,
                t.primary_type,
                d.district,
                CAST(ti.year AS VARCHAR) AS year
            FROM read_parquet('{fact}') AS f
            LEFT JOIN read_parquet('{tipo}') AS t
                ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(t.id AS BIGINT)
            LEFT JOIN read_parquet('{dist}') AS d
                ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
            LEFT JOIN read_parquet('{tiempo}') AS ti
                ON CAST(f.fk_tiempo AS BIGINT) = CAST(ti.id AS BIGINT)
            ORDER BY CAST(f.id AS BIGINT) DESC
            LIMIT {int(limit)}
        """
        df = con.execute(sql).fetchdf()
        items = []
        for _, row in df.iterrows():
            items.append(
                {
                    "id": row.get("id"),
                    "legacy_id": row.get("legacy_id"),
                    "expand": {
                        "tipo_crimen": {"primary_type": row.get("primary_type")},
                        "distrito": {"district": row.get("district")},
                        "tiempo": {"year": row.get("year")},
                    },
                }
            )
        return items

    def dimension_counts(self) -> list[dict[str, Any]]:
        result = []
        for slug in DIM_COLLECTIONS:
            meta = COLLECTIONS.get(slug, {})
            result.append(
                {
                    "slug": slug,
                    "label": meta.get("label", slug),
                    "value": self.count_dimension(slug),
                }
            )
        result.sort(key=lambda x: x["value"], reverse=True)
        return result

    def build_dashboard_payload(self) -> dict[str, Any]:
        t0 = time.perf_counter()
        with PocketBaseClient() as pb:
            pb.auth_admin()
            raw_count = pb.count_records("crimes_220k")

        totals = {
            "crimes_220k": raw_count,
            "fact_crimes": self.count_fact_crimes(),
            "dim_caso": self.count_dimension("dim_caso"),
            "dim_tipo_crimen": self.count_dimension("dim_tipo_crimen"),
            "dim_distrito_policial": self.count_dimension("dim_distrito_policial"),
        }
        dim_counts = self.dimension_counts()
        recent_facts = self.recent_facts(limit=8)
        crimes_by_dist = self.crimes_by_district(limit=10)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "totals": totals,
            "recent_facts": recent_facts,
            "dimension_counts": dim_counts[:10],
            "crimes_by_district": crimes_by_dist,
            "service": "CrimeTrack Analytics Corp",
            "architecture": {
                "pocketbase": ["crimes_220k"],
                "minio": "Parquet particionado (year/month) + DuckDB",
                "cache_ttl_seconds": DASHBOARD_CACHE_TTL,
            },
            "performance": {
                "dashboard_query_ms": elapsed_ms,
                "engine": "duckdb",
            },
        }


def get_cached_dashboard_stats() -> dict[str, Any]:
    from django.core.cache import cache

    cached = cache.get(DASHBOARD_CACHE_KEY)
    if cached is not None:
        cached = dict(cached)
        cached["from_cache"] = True
        return cached

    payload = AnalyticsService().build_dashboard_payload()
    payload["from_cache"] = False
    cache.set(DASHBOARD_CACHE_KEY, payload, DASHBOARD_CACHE_TTL)
    return payload


def invalidate_dashboard_cache() -> None:
    from django.core.cache import cache

    cache.delete(DASHBOARD_CACHE_KEY)
