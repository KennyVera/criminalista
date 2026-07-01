from django.urls import path

from packages.dashboard_analitica.tactical_views import (
    ByEvidenceView,
    ByPatrolView,
    ByStateView,
    ByTypeView,
    ByUserView,
    ByZoneView,
    StrategicSummaryView,
    TacticalHealthView,
    TrendsView,
)
from packages.dashboard_analitica.views import (
    DashboardCrimeForecastView,
    DashboardDetectiveRankingView,
    DashboardDirectAccessManifestView,
    DashboardDirectAccessPreviewView,
    DashboardFilterOptionsView,
    DashboardFilteredStatsView,
    DashboardHeatMapView,
    DashboardOperationalIndicatorsView,
    DashboardOverviewView,
)

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("filtros/opciones/", DashboardFilterOptionsView.as_view(), name="dashboard-filtros-opciones"),
    path("filtros/", DashboardFilteredStatsView.as_view(), name="dashboard-filtros"),
    path("mapa-calor/", DashboardHeatMapView.as_view(), name="dashboard-mapa-calor"),
    path(
        "ranking-detectives/",
        DashboardDetectiveRankingView.as_view(),
        name="dashboard-ranking-detectives",
    ),
    path(
        "indicadores-operativos/",
        DashboardOperationalIndicatorsView.as_view(),
        name="dashboard-indicadores-operativos",
    ),
    path(
        "prediccion/",
        DashboardCrimeForecastView.as_view(),
        name="dashboard-prediccion",
    ),
    path(
        "direct-access/manifest/",
        DashboardDirectAccessManifestView.as_view(),
        name="dashboard-direct-manifest",
    ),
    path(
        "direct-access/preview/",
        DashboardDirectAccessPreviewView.as_view(),
        name="dashboard-direct-preview",
    ),
    # --- Capa TÁCTICA / ESTRATÉGICA (ClickHouse) ---
    path("tactico/health/", TacticalHealthView.as_view(), name="tactico-health"),
    path("tactico/resumen/", StrategicSummaryView.as_view(), name="tactico-resumen"),
    path("tactico/tendencias/", TrendsView.as_view(), name="tactico-tendencias"),
    path("tactico/por-zona/", ByZoneView.as_view(), name="tactico-por-zona"),
    path("tactico/por-tipo/", ByTypeView.as_view(), name="tactico-por-tipo"),
    path("tactico/por-estado/", ByStateView.as_view(), name="tactico-por-estado"),
    path("tactico/por-usuario/", ByUserView.as_view(), name="tactico-por-usuario"),
    path("tactico/por-patrulla/", ByPatrolView.as_view(), name="tactico-por-patrulla"),
    path("tactico/por-evidencia/", ByEvidenceView.as_view(), name="tactico-por-evidencia"),
]
