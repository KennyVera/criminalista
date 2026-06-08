"""
Motor analítico del paquete Dashboard — DuckDB + Parquet en MinIO.
"""

from __future__ import annotations

import time
from typing import Any

from core.collections_meta import COLLECTIONS
from core.services.analytics_service import (
    DASHBOARD_CACHE_KEY,
    DASHBOARD_CACHE_TTL,
    AnalyticsService,
    invalidate_dashboard_cache,
)
from core.services.minio_store import DIM_COLLECTIONS

__all__ = [
    "DashboardAnalyticsEngine",
    "DASHBOARD_CACHE_KEY",
    "DASHBOARD_CACHE_TTL",
    "get_cached_dashboard_stats",
    "invalidate_dashboard_cache",
]


class DashboardAnalyticsEngine(AnalyticsService):
    """Extensiones para casos de uso del diagrama Dashboard y Analítica Criminal."""

    def _fact_filters_sql(
        self,
        *,
        distrito: str | None = None,
        tipo: str | None = None,
        year: str | None = None,
        month: str | None = None,
    ) -> tuple[str, str]:
        """Devuelve (joins extra, condiciones WHERE)."""
        joins = ""
        conditions: list[str] = []
        if distrito:
            joins += f"""
            INNER JOIN read_parquet('{self._dim_parquet("dim_distrito_policial")}') AS d
                ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
            """
            safe = distrito.replace("'", "''")
            conditions.append(
                f"(CAST(d.district AS VARCHAR) = '{safe}' OR CAST(d.beat AS VARCHAR) = '{safe}')"
            )
        if tipo:
            joins += f"""
            INNER JOIN read_parquet('{self._dim_parquet("dim_tipo_crimen")}') AS tc
                ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(tc.id AS BIGINT)
            """
            safe = tipo.replace("'", "''")
            conditions.append(f"CAST(tc.primary_type AS VARCHAR) = '{safe}'")
        if year or month:
            joins += f"""
            INNER JOIN read_parquet('{self._dim_parquet("dim_tiempo")}') AS ti
                ON CAST(f.fk_tiempo AS BIGINT) = CAST(ti.id AS BIGINT)
            """
            if year:
                conditions.append(f"CAST(ti.year AS VARCHAR) = '{year.replace(chr(39), '')}'")
            if month:
                conditions.append(f"CAST(ti.month AS VARCHAR) = '{month.replace(chr(39), '')}'")
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        return joins, where

    def filter_options(self) -> dict[str, Any]:
        """Valores distintos en dimensiones para combos del dashboard."""
        con = self.connection()
        dist = self._dim_parquet("dim_distrito_policial")
        tipo = self._dim_parquet("dim_tipo_crimen")
        tiempo = self._dim_parquet("dim_tiempo")

        distritos = [
            str(r[0])
            for r in con.execute(
                f"""
                SELECT DISTINCT CAST(district AS VARCHAR) AS v
                FROM read_parquet('{dist}')
                WHERE district IS NOT NULL
                  AND TRIM(CAST(district AS VARCHAR)) != ''
                ORDER BY v
                """
            ).fetchall()
        ]
        tipos = [
            str(r[0])
            for r in con.execute(
                f"""
                SELECT DISTINCT CAST(primary_type AS VARCHAR) AS v
                FROM read_parquet('{tipo}')
                WHERE primary_type IS NOT NULL
                  AND TRIM(CAST(primary_type AS VARCHAR)) != ''
                ORDER BY v
                """
            ).fetchall()
        ]
        anios = [
            str(r[0])
            for r in con.execute(
                f"""
                SELECT DISTINCT CAST(year AS VARCHAR) AS v
                FROM read_parquet('{tiempo}')
                WHERE year IS NOT NULL
                  AND TRIM(CAST(year AS VARCHAR)) != ''
                ORDER BY v
                """
            ).fetchall()
        ]
        meses_raw = con.execute(
            f"""
            SELECT DISTINCT CAST(month AS INTEGER) AS m
            FROM read_parquet('{tiempo}')
            WHERE month IS NOT NULL
            ORDER BY m
            """
        ).fetchall()
        mes_nombres = [
            "",
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        meses = [
            {"value": str(m), "label": f"{m} — {mes_nombres[m]}" if 1 <= m <= 12 else str(m)}
            for (m,) in meses_raw
            if m is not None
        ]

        return {
            "distritos": distritos,
            "tipos_delito": tipos,
            "anios": anios,
            "meses": meses,
        }

    def crimes_by_district_filtered(self, *, limit: int = 10, **filters) -> list[dict[str, Any]]:
        con = self.connection()
        fact = self._fact_parquet_source()
        dist_path = self._dim_parquet("dim_distrito_policial")
        joins, where = self._fact_filters_sql(**filters)
        if "dim_distrito_policial" not in joins:
            joins += f"""
            INNER JOIN read_parquet('{dist_path}') AS d
                ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
            """
        sql = f"""
            SELECT
                CAST(d.district AS VARCHAR) AS district,
                CAST(d.beat AS VARCHAR) AS beat,
                COUNT(*)::BIGINT AS total_crimes
            FROM read_parquet('{fact}') AS f
            {joins}
            {where}
            GROUP BY d.district, d.beat
            ORDER BY total_crimes DESC
            LIMIT {int(limit)}
        """
        return con.execute(sql).fetchdf().to_dict(orient="records")

    def filtered_crime_count(
        self,
        *,
        distrito: str | None = None,
        tipo: str | None = None,
        year: str | None = None,
        month: str | None = None,
    ) -> int:
        con = self.connection()
        fact = self._fact_parquet_source()
        joins, where = self._fact_filters_sql(
            distrito=distrito, tipo=tipo, year=year, month=month
        )
        row = con.execute(
            f"SELECT COUNT(*)::BIGINT FROM read_parquet('{fact}') AS f {joins}{where}"
        ).fetchone()
        return int(row[0]) if row else 0

    def crimes_by_type(self, *, limit: int = 12, **filters) -> list[dict[str, Any]]:
        con = self.connection()
        fact = self._fact_parquet_source()
        tipo = self._dim_parquet("dim_tipo_crimen")
        extra_joins, where = self._fact_filters_sql(**filters)
        sql = f"""
            SELECT
                CAST(t.primary_type AS VARCHAR) AS label,
                COUNT(*)::BIGINT AS value
            FROM read_parquet('{fact}') AS f
            INNER JOIN read_parquet('{tipo}') AS t
                ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(t.id AS BIGINT)
            {extra_joins}
            {where}
            GROUP BY t.primary_type
            ORDER BY value DESC
            LIMIT {int(limit)}
        """
        df = con.execute(sql).fetchdf()
        return df.to_dict(orient="records")

    def crimes_trend_by_year(self, **filters) -> list[dict[str, Any]]:
        con = self.connection()
        fact = self._fact_parquet_source()
        tiempo = self._dim_parquet("dim_tiempo")
        fcopy = dict(filters)
        year = fcopy.pop("year", None)
        month = fcopy.pop("month", None)
        joins, where = self._fact_filters_sql(**fcopy)
        extra: list[str] = []
        if year:
            extra.append(f"CAST(ti.year AS VARCHAR) = '{str(year).replace(chr(39), '')}'")
        if month:
            extra.append(f"CAST(ti.month AS VARCHAR) = '{str(month).replace(chr(39), '')}'")
        if extra:
            clause = " AND ".join(extra)
            where = f"{where} AND {clause}" if where else f" WHERE {clause}"
        sql = f"""
            SELECT CAST(ti.year AS VARCHAR) AS label, COUNT(*)::BIGINT AS value
            FROM read_parquet('{fact}') AS f
            INNER JOIN read_parquet('{tiempo}') AS ti
                ON CAST(f.fk_tiempo AS BIGINT) = CAST(ti.id AS BIGINT)
            {joins}
            {where}
            GROUP BY ti.year
            ORDER BY label
        """
        df = con.execute(sql).fetchdf()
        return df.to_dict(orient="records")

    def heat_map_by_district(self, *, limit: int = 15, **filters) -> list[dict[str, Any]]:
        data = self.crimes_by_district(limit=limit)
        items = data.get("items", [])
        if not items:
            return []
        max_val = max(int(i.get("total_crimes", 0) or 0) for i in items) or 1
        for row in items:
            total = int(row.get("total_crimes", 0) or 0)
            row["intensity"] = round(total / max_val, 3)
            row["label"] = f"Distrito {row.get('district', '—')}"
        return items

    def detective_ranking(self, *, limit: int = 10) -> list[dict[str, Any]]:
        from packages.dashboard_analitica.services.detective_ranking_service import (
            detective_ranking_from_assignments,
        )

        try:
            return detective_ranking_from_assignments(limit=limit)
        except Exception:
            return []

    def operational_indicators(self) -> dict[str, Any]:
        con = self.connection()
        caso = self._dim_parquet("dim_caso")
        fact = self._fact_parquet_source()
        t0 = time.perf_counter()
        trend = self.crimes_trend_by_year()
        res_sql = f"""
            SELECT
                COUNT(*)::BIGINT AS total_casos,
                SUM(
                    CASE
                        WHEN LOWER(CAST(estado_caso AS VARCHAR)) IN (
                            'cerrado', 'resuelto', 'closed', 'resuelta', 'cerrada'
                        ) THEN 1 ELSE 0
                    END
                )::BIGINT AS casos_resueltos
            FROM read_parquet('{caso}')
        """
        res_row = con.execute(res_sql).fetchone()
        total_casos = int(res_row[0]) if res_row else 0
        casos_resueltos = int(res_row[1]) if res_row and res_row[1] else 0
        tasa = round((casos_resueltos / total_casos * 100) if total_casos else 0, 2)
        fact_count = self.count_fact_crimes()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "tendencias_delictivas": trend,
            "tasa_resolucion": {
                "porcentaje": tasa,
                "casos_resueltos": casos_resueltos,
                "total_casos": total_casos,
            },
            "hechos_registrados": fact_count,
            "query_ms": elapsed_ms,
        }

    def build_dashboard_payload(self) -> dict[str, Any]:
        """Construye payload completo desde MinIO OLAP (sin PocketBase)."""
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
        crimes_by_type = self.crimes_by_type(limit=8)
        heat_map = self.heat_map_by_district(limit=12)
        detective_ranking = self.detective_ranking(limit=8)
        operational = self.operational_indicators()

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "totals": totals,
            "recent_facts": recent_facts,
            "dimension_counts": dim_counts[:10],
            "crimes_by_district": crimes_by_dist,
            "crimes_by_type": crimes_by_type,
            "heat_map": heat_map,
            "detective_ranking": detective_ranking,
            "operational_indicators": operational,
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
