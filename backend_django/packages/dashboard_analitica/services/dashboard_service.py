"""
DashboardService — lectura desde app_dashboard_summary (OLAP precalculado).
"""

from __future__ import annotations

import time
from typing import Any

from packages.dashboard_analitica.services.dashboard_summary_store import DashboardSummaryStore
from packages.dashboard_analitica.services.detective_ranking_service import live_investigation_metrics
from packages.dashboard_analitica.services.summary_materializer import (
    filtered_stats_from_summary,
    materialize_dashboard_summary,
)


class DashboardService:
    def __init__(self) -> None:
        self.store = DashboardSummaryStore()

    def _ensure_or_materialize(self) -> None:
        if not self.store.is_ready():
            materialize_dashboard_summary()

    @staticmethod
    def _patch_live_investigation(payload: dict[str, Any]) -> dict[str, Any]:
        live = live_investigation_metrics(ranking_limit=15)
        patched = dict(payload)
        patched["detective_ranking"] = live["detective_ranking"]
        op = dict(patched.get("operational_indicators") or {})
        op["tasa_resolucion"] = {
            **dict(op.get("tasa_resolucion") or {}),
            **live["tasa_resolucion"],
        }
        patched["operational_indicators"] = op
        patched["investigation_metrics_live"] = True
        return patched

    def overview(self) -> dict[str, Any]:
        from django.core.cache import cache

        from core.services.analytics_service import DASHBOARD_CACHE_KEY, DASHBOARD_CACHE_TTL

        cached = cache.get(DASHBOARD_CACHE_KEY)
        if cached:
            out = dict(cached)
            out["from_cache"] = True
            return out

        t0 = time.perf_counter()
        self._ensure_or_materialize()
        payload = self.store.get_payload("overview")
        if not payload:
            raise RuntimeError(
                "No hay resumen de dashboard. Ejecute: python manage.py refresh_dashboard_summary"
            )
        payload = self._patch_live_investigation(dict(payload))
        meta = self.store.get_meta()
        payload["from_materialized_summary"] = True
        payload["summary_updated_at"] = meta.get("updated_at")
        payload["performance"] = {
            **(payload.get("performance") or {}),
            "dashboard_query_ms": round((time.perf_counter() - t0) * 1000, 3),
            "engine": "app_dashboard_summary",
        }
        cache.set(DASHBOARD_CACHE_KEY, payload, DASHBOARD_CACHE_TTL)
        return payload

    def filter_options(self) -> dict[str, Any]:
        from django.core.cache import cache

        cache_key = "crimetrack:dashboard:filter_options:v1"
        cached = cache.get(cache_key)
        if cached:
            return {**dict(cached), "_from_cache": True}

        self._ensure_or_materialize()
        data = self.store.get_payload("filter_options")
        if data:
            out = dict(data)
            cache.set(cache_key, out, 60 * 15)
            return out
        from packages.dashboard_analitica.services.analytics_engine import (
            DashboardAnalyticsEngine,
        )

        out = DashboardAnalyticsEngine().filter_options()
        cache.set(cache_key, out, 60 * 15)
        return out

    def filtered_stats(
        self,
        *,
        distrito: str | None = None,
        tipo: str | None = None,
        year: str | None = None,
        month: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_or_materialize()
        if self.store.get_payload("agg_rollups"):
            return filtered_stats_from_summary(
                distrito=distrito, tipo=tipo, year=year, month=month
            )
        from packages.dashboard_analitica.services.analytics_engine import (
            DashboardAnalyticsEngine,
        )

        engine = DashboardAnalyticsEngine()
        filters = {
            k: v
            for k, v in {
                "distrito": distrito,
                "tipo": tipo,
                "year": year,
                "month": month,
            }.items()
            if v
        }
        return {
            "filters_applied": filters,
            "total_hechos": engine.filtered_crime_count(**filters),
            "por_tipo": engine.crimes_by_type(limit=10, **filters),
            "por_anio": engine.crimes_trend_by_year(**filters),
            "por_distrito": engine.crimes_by_district_filtered(limit=10, **filters),
            "source": "duckdb_fallback",
        }

    def heat_map(self, **filters) -> dict[str, Any]:
        self._ensure_or_materialize()
        data = self.store.get_payload("heat_map")
        if data and not filters:
            return dict(data)
        from packages.dashboard_analitica.services.analytics_engine import (
            DashboardAnalyticsEngine,
        )

        return {"items": DashboardAnalyticsEngine().heat_map_by_district(limit=15, **filters)}

    def detective_ranking(self) -> dict[str, Any]:
        live = live_investigation_metrics(ranking_limit=15)
        return {
            "items": live["detective_ranking"],
            "source": "live",
            "tasa_resolucion": live["tasa_resolucion"],
        }

    def operational_indicators(self) -> dict[str, Any]:
        self._ensure_or_materialize()
        data = self.store.get_payload("operational")
        if not data:
            from packages.dashboard_analitica.services.analytics_engine import (
                DashboardAnalyticsEngine,
            )

            data = DashboardAnalyticsEngine().operational_indicators()
        else:
            data = dict(data)
        live = live_investigation_metrics(ranking_limit=15)
        data["tasa_resolucion"] = {
            **dict(data.get("tasa_resolucion") or {}),
            **live["tasa_resolucion"],
        }
        data["investigation_metrics_live"] = True
        return data
