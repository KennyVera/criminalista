"""
Consultas analiticas ultrarrapidas: DuckDB lee Parquet en MinIO via S3 (sin cargar todo en RAM).
"""

from __future__ import annotations

import time
from typing import Any

from core.collections_meta import COLLECTIONS
from core.services.duckdb_s3 import DuckDBS3Session
from core.services.minio_store import DIM_COLLECTIONS, MinioParquetStore

DASHBOARD_CACHE_KEY = "crimetrack:dashboard:stats:v3"
DASHBOARD_CACHE_TTL = 60 * 15  # 15 minutos


class AnalyticsService:
    def __init__(self, store: MinioParquetStore | None = None):
        self.store = store or MinioParquetStore()
        self._duck = DuckDBS3Session(self.store)

    def _s3_uri(self, key_or_glob: str) -> str:
        return self._duck.s3_uri(key_or_glob)

    def connection(self):
        return self._duck.connection()

    def _fact_parquet_source(self) -> str:
        return self._duck.fact_parquet_source()

    def _dim_parquet(self, collection: str) -> str:
        return self._duck.dim_parquet(collection)

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

    def lookup_hechos_by_case_numbers(
        self, case_numbers: list[str]
    ) -> dict[str, dict[str, Any]]:
        """
        Detalle del hecho por número de caso desde star schema OLAP (fact consolidado + dims).
        Clave del dict: case_number en mayúsculas.
        """
        cleaned = [
            str(cn).strip().replace("'", "''")
            for cn in case_numbers
            if cn is not None and str(cn).strip()
        ]
        if not cleaned:
            return {}

        in_list = ", ".join(f"'{cn.upper()}'" for cn in cleaned)
        fact = self._fact_parquet_source()
        dim_caso = self._dim_parquet("dim_caso")
        dim_tipo = self._dim_parquet("dim_tipo_crimen")
        dim_dist = self._dim_parquet("dim_distrito_policial")
        dim_area = self._dim_parquet("dim_area_administrativa")
        dim_tiempo = self._dim_parquet("dim_tiempo")
        dim_lugar = self._dim_parquet("dim_ubicacion_lugar")
        dim_geo = self._dim_parquet("dim_ubicacion_geografica")
        dim_arrest = self._dim_parquet("dim_arresto")
        dim_dom = self._dim_parquet("dim_violencia_domestica")

        sql = f"""
            SELECT
                UPPER(TRIM(CAST(dc.case_number AS VARCHAR))) AS cn,
                CAST(t.primary_type AS VARCHAR) AS primary_type,
                CAST(t.description AS VARCHAR) AS description,
                CAST(t.iucr AS VARCHAR) AS iucr,
                CAST(t.fbi_code AS VARCHAR) AS fbi_code,
                CAST(d.district AS VARCHAR) AS district,
                CAST(d.beat AS VARCHAR) AS beat,
                CAST(a.ward AS VARCHAR) AS ward,
                CAST(a.community_area AS VARCHAR) AS community_area,
                CAST(tm.date AS VARCHAR) AS date,
                CAST(tm.year AS VARCHAR) AS year,
                CAST(l.location_description AS VARCHAR) AS location_description,
                CAST(l.block AS VARCHAR) AS block,
                CAST(g.latitude AS VARCHAR) AS latitude,
                CAST(g.longitude AS VARCHAR) AS longitude,
                CAST(g.location AS VARCHAR) AS location,
                CAST(ar.arrest AS VARCHAR) AS arrest,
                CAST(vd.domestic AS VARCHAR) AS domestic,
                CAST(dc.estado_caso AS VARCHAR) AS estado_caso,
                CAST(dc.prioridad_caso AS VARCHAR) AS prioridad_caso,
                CAST(dc.fecha_reporte AS VARCHAR) AS fecha_reporte,
                CAST(dc.observaciones AS VARCHAR) AS observaciones,
                CAST(dc.investigador_asignado AS VARCHAR) AS investigador_asignado
            FROM read_parquet('{dim_caso}') AS dc
            INNER JOIN read_parquet('{fact}') AS f
                ON CAST(f.fk_caso AS BIGINT) = CAST(dc.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_tipo}') AS t
                ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(t.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_dist}') AS d
                ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_area}') AS a
                ON CAST(f.fk_area AS BIGINT) = CAST(a.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_tiempo}') AS tm
                ON CAST(f.fk_tiempo AS BIGINT) = CAST(tm.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_lugar}') AS l
                ON CAST(f.fk_ubicacion_lugar AS BIGINT) = CAST(l.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_geo}') AS g
                ON CAST(f.fk_ubicacion_geo AS BIGINT) = CAST(g.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_arrest}') AS ar
                ON CAST(f.fk_arresto AS BIGINT) = CAST(ar.id AS BIGINT)
            LEFT JOIN read_parquet('{dim_dom}') AS vd
                ON CAST(f.fk_domestico AS BIGINT) = CAST(vd.id AS BIGINT)
            WHERE UPPER(TRIM(CAST(dc.case_number AS VARCHAR))) IN ({in_list})
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY UPPER(TRIM(CAST(dc.case_number AS VARCHAR)))
                ORDER BY CAST(f.id AS BIGINT) DESC
            ) = 1
        """
        con = self.connection()
        try:
            df = con.execute(sql).fetchdf()
        except Exception:
            return {}

        out: dict[str, dict[str, Any]] = {}
        for row in df.to_dict(orient="records"):
            cn = str(row.get("cn") or "").upper()
            if cn:
                out[cn] = {k: v for k, v in row.items() if k != "cn" and v is not None}
        return out

    def lookup_hecho_by_case_number(self, case_number: str) -> dict[str, Any] | None:
        cn = str(case_number or "").strip()
        if not cn:
            return None
        return self.lookup_hechos_by_case_numbers([cn]).get(cn.upper())

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
        fact_count = self.count_fact_crimes()

        totals = {
            "crimes_220k": fact_count,
            "fact_crimes": fact_count,
            "dim_caso": self.count_dimension("dim_caso"),
            "dim_tipo_crimen": self.count_dimension("dim_tipo_crimen"),
            "dim_distrito_policial": self.count_dimension("dim_distrito_policial"),
            "source": "minio_olap",
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
                "pocketbase": "OLTP — no consultado en dashboard",
                "minio": "Parquet OLAP + app_dashboard_summary",
                "cache_ttl_seconds": DASHBOARD_CACHE_TTL,
            },
            "performance": {
                "dashboard_query_ms": elapsed_ms,
                "engine": "duckdb",
            },
        }


def get_cached_dashboard_stats() -> dict[str, Any]:
    from packages.dashboard_analitica.services.dashboard_service import DashboardService

    return DashboardService().overview()


def invalidate_dashboard_cache() -> None:
    from django.core.cache import cache

    cache.delete(DASHBOARD_CACHE_KEY)
    cache.delete("crimetrack:dashboard:filter_options:v1")
    cache.delete("crimetrack:dashboard:filtered:v1")
