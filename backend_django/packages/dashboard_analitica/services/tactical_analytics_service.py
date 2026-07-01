"""
TacticalStrategicAnalyticsService — consultas OLAP tácticas/estratégicas.

Capa ANALÍTICA, separada del CRUD operativo:
    ClickHouse  ->  TacticalStrategicAnalyticsService  ->  dashboard/reportes

Todas las consultas son de SOLO LECTURA contra crimetrack_analytics (ClickHouse).
Si ClickHouse no responde o una tabla aún no tiene datos, los métodos degradan
con gracia devolviendo `items: []` y un `source` indicando el estado, sin
romper el endpoint ni tocar la capa operativa de MinIO.
"""

from __future__ import annotations

import time
from typing import Any

from core.services.clickhouse_client import ClickHouseService

FACT_TABLES = [
    "fact_crimes",
    "fact_incidentes",
    "fact_expedientes",
    "fact_evidencias",
    "fact_auditoria",
]
DIM_TABLES = [
    "dim_fecha",
    "dim_tipo_crimen",
    "dim_ubicacion",
    "dim_usuario",
    "dim_estado",
    "dim_patrulla",
]
ANALYTICS_TABLES = FACT_TABLES + DIM_TABLES


class TacticalStrategicAnalyticsService:
    def __init__(self, ch: ClickHouseService | None = None) -> None:
        self.ch = ch or ClickHouseService()

    # -- utilidades -------------------------------------------------------
    def available(self) -> bool:
        return self.ch.ping()

    def _safe(self, fn, *, default: Any = None):
        """Ejecuta una consulta devolviendo (data, query_ms) o degradando."""
        t0 = time.perf_counter()
        try:
            data = fn()
            ms = round((time.perf_counter() - t0) * 1000, 2)
            return data, ms, "clickhouse"
        except Exception as exc:  # noqa: BLE001 - degradar con gracia
            ms = round((time.perf_counter() - t0) * 1000, 2)
            return (default if default is not None else []), ms, f"unavailable:{exc}"

    # -- salud / estado ---------------------------------------------------
    def health(self) -> dict[str, Any]:
        ok = self.available()
        counts = self.ch.table_counts(ANALYTICS_TABLES) if ok else {}
        return {
            "clickhouse": "up" if ok else "down",
            "database": self.ch.database,
            "host": f"{self.ch.host}:{self.ch.port}",
            "tables": counts,
            "layer": "tactica_estrategica",
        }

    # -- resumen estratégico ---------------------------------------------
    def resumen_estrategico(self) -> dict[str, Any]:
        def run() -> dict[str, Any]:
            counts = self.ch.table_counts(ANALYTICS_TABLES)
            return counts

        data, ms, source = self._safe(run, default={})
        return {
            "totales": data,
            "query_ms": ms,
            "source": source,
        }

    # -- tendencias temporales (estratégico) -----------------------------
    def tendencia_temporal(self, *, distrito: str | None = None, tipo: str | None = None) -> dict[str, Any]:
        def run() -> list[dict[str, Any]]:
            where = ["year > 0"]
            params: dict[str, Any] = {}
            if distrito:
                where.append("district = {distrito:String}")
                params["distrito"] = distrito
            if tipo:
                where.append("primary_type = {tipo:String}")
                params["tipo"] = tipo
            sql = f"""
                SELECT year, count() AS total
                FROM fact_crimes
                WHERE {' AND '.join(where)}
                GROUP BY year
                ORDER BY year
            """
            return self.ch.query(sql, params)

        items, ms, source = self._safe(run)
        return {"items": items, "query_ms": ms, "source": source}

    # -- estadística por zona (táctico) ----------------------------------
    def por_zona(self, *, limit: int = 20) -> dict[str, Any]:
        def run() -> list[dict[str, Any]]:
            sql = """
                SELECT district, beat, count() AS total
                FROM fact_crimes
                GROUP BY district, beat
                ORDER BY total DESC
                LIMIT {limit:UInt32}
            """
            return self.ch.query(sql, {"limit": int(limit)})

        items, ms, source = self._safe(run)
        return {"items": items, "query_ms": ms, "source": source}

    # -- estadística por tipo de crimen (táctico) ------------------------
    def por_tipo(self, *, limit: int = 20) -> dict[str, Any]:
        def run() -> list[dict[str, Any]]:
            sql = """
                SELECT primary_type, count() AS total
                FROM fact_crimes
                GROUP BY primary_type
                ORDER BY total DESC
                LIMIT {limit:UInt32}
            """
            return self.ch.query(sql, {"limit": int(limit)})

        items, ms, source = self._safe(run)
        return {"items": items, "query_ms": ms, "source": source}

    # -- estadística por estado (expedientes/incidentes) -----------------
    def por_estado(self, *, ambito: str = "expediente") -> dict[str, Any]:
        tabla = {
            "expediente": "fact_expedientes",
            "incidente": "fact_incidentes",
        }.get(ambito, "fact_expedientes")

        def run() -> list[dict[str, Any]]:
            sql = f"""
                SELECT estado, count() AS total
                FROM {tabla}
                GROUP BY estado
                ORDER BY total DESC
            """
            return self.ch.query(sql)

        items, ms, source = self._safe(run)
        return {"ambito": ambito, "tabla": tabla, "items": items, "query_ms": ms, "source": source}

    # -- actividad por usuario (auditoría) -------------------------------
    def por_usuario(self, *, limit: int = 20) -> dict[str, Any]:
        def run() -> list[dict[str, Any]]:
            sql = """
                SELECT fk_usuario, count() AS eventos
                FROM fact_auditoria
                GROUP BY fk_usuario
                ORDER BY eventos DESC
                LIMIT {limit:UInt32}
            """
            return self.ch.query(sql, {"limit": int(limit)})

        items, ms, source = self._safe(run)
        return {"items": items, "query_ms": ms, "source": source}

    # -- incidentes por patrulla (táctico) -------------------------------
    def por_patrulla(self, *, limit: int = 20) -> dict[str, Any]:
        def run() -> list[dict[str, Any]]:
            sql = """
                SELECT patrulla_codigo, count() AS incidentes
                FROM fact_incidentes
                WHERE patrulla_codigo != ''
                GROUP BY patrulla_codigo
                ORDER BY incidentes DESC
                LIMIT {limit:UInt32}
            """
            return self.ch.query(sql, {"limit": int(limit)})

        items, ms, source = self._safe(run)
        return {"items": items, "query_ms": ms, "source": source}

    # -- evidencias por estado de custodia (táctico) ---------------------
    def por_evidencia(self) -> dict[str, Any]:
        def run() -> list[dict[str, Any]]:
            sql = """
                SELECT estado_custodia, tipo_evidencia, count() AS total
                FROM fact_evidencias
                GROUP BY estado_custodia, tipo_evidencia
                ORDER BY total DESC
            """
            return self.ch.query(sql)

        items, ms, source = self._safe(run)
        return {"items": items, "query_ms": ms, "source": source}
