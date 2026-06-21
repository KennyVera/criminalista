from django.urls import path

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
]
