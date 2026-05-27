from __future__ import annotations

from typing import Any

from packages.dashboard_analitica.services.analytics_engine import DashboardAnalyticsEngine


class DashboardService:
    def __init__(self) -> None:
        self.engine = DashboardAnalyticsEngine()

    def overview(self) -> dict[str, Any]:
        from packages.dashboard_analitica.services.analytics_engine import get_cached_dashboard_stats

        return get_cached_dashboard_stats()

    def filter_options(self) -> dict[str, Any]:
        return self.engine.filter_options()

    def filtered_stats(
        self,
        *,
        distrito: str | None = None,
        tipo: str | None = None,
        year: str | None = None,
        month: str | None = None,
    ) -> dict[str, Any]:
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
            "total_hechos": self.engine.filtered_crime_count(**filters),
            "por_tipo": self.engine.crimes_by_type(limit=10, **filters),
            "por_anio": self.engine.crimes_trend_by_year(**filters),
            "por_distrito": self.engine.crimes_by_district_filtered(limit=10, **filters),
        }

    def heat_map(self, **filters) -> dict[str, Any]:
        return {"items": self.engine.heat_map_by_district(limit=15, **filters)}

    def detective_ranking(self) -> dict[str, Any]:
        return {"items": self.engine.detective_ranking(limit=10)}

    def operational_indicators(self) -> dict[str, Any]:
        return self.engine.operational_indicators()
