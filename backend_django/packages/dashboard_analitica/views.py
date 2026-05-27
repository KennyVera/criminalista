from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.pocketbase import PocketBaseError
from packages.dashboard_analitica.permissions import IsAnalistaCriminalJWT, IsDashboardViewerJWT
from packages.dashboard_analitica.services.dashboard_service import DashboardService


def _minio_error(exc: Exception):
    return Response(
        {"error": str(exc), "detail": "MinIO / DuckDB"},
        status=status.HTTP_502_BAD_GATEWAY,
    )


@method_decorator(csrf_exempt, name="dispatch")
class DashboardOverviewView(APIView):
    """Visualizar dashboard estadístico — KPIs, gráficas, mapa, ranking."""

    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        try:
            return Response(DashboardService().overview())
        except PocketBaseError as exc:
            return Response({"error": str(exc)}, status=502)
        except Exception as exc:
            return _minio_error(exc)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardFilterOptionsView(APIView):
    """Opciones para combos de filtro (distritos, tipos, años, meses)."""

    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        try:
            return Response(DashboardService().filter_options())
        except Exception as exc:
            return _minio_error(exc)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardFilteredStatsView(APIView):
    """Filtrar estadísticas por zona, tipo de delito y fecha."""

    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        try:
            data = DashboardService().filtered_stats(
                distrito=request.query_params.get("zona") or None,
                tipo=request.query_params.get("tipo") or None,
                year=request.query_params.get("anio") or None,
                month=request.query_params.get("mes") or None,
            )
            return Response(data)
        except Exception as exc:
            return _minio_error(exc)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardHeatMapView(APIView):
    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        try:
            return Response(DashboardService().heat_map())
        except Exception as exc:
            return _minio_error(exc)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardDetectiveRankingView(APIView):
    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        try:
            return Response(DashboardService().detective_ranking())
        except Exception as exc:
            return _minio_error(exc)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardOperationalIndicatorsView(APIView):
    """Generar indicadores operativos — solo Analista Criminal / Admin."""

    permission_classes = [IsAnalistaCriminalJWT]

    def get(self, request):
        try:
            return Response(DashboardService().operational_indicators())
        except Exception as exc:
            return _minio_error(exc)
