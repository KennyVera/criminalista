"""
Endpoints TÁCTICOS / ESTRATÉGICOS — consultan ClickHouse (capa analítica).

Flujo:  ClickHouse -> TacticalStrategicAnalyticsService -> estos endpoints.

Estos endpoints son independientes de los endpoints operativos del dashboard
(que siguen leyendo MinIO/DuckDB), de modo que la capa operativa no se rompe.
Si ClickHouse aún no tiene datos, responden con `source` indicando el estado.
"""

from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.dashboard_analitica.permissions import IsAnalistaCriminalJWT, IsDashboardViewerJWT
from packages.dashboard_analitica.services.tactical_analytics_service import (
    TacticalStrategicAnalyticsService,
)


@method_decorator(csrf_exempt, name="dispatch")
class TacticalHealthView(APIView):
    """Estado de la capa analítica ClickHouse + conteos por tabla."""

    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        return Response(TacticalStrategicAnalyticsService().health())


@method_decorator(csrf_exempt, name="dispatch")
class StrategicSummaryView(APIView):
    """Resumen estratégico: totales por tabla analítica (solo Analista/Admin)."""

    permission_classes = [IsAnalistaCriminalJWT]

    def get(self, request):
        return Response(TacticalStrategicAnalyticsService().resumen_estrategico())


@method_decorator(csrf_exempt, name="dispatch")
class TrendsView(APIView):
    """Tendencias temporales de criminalidad (OLAP)."""

    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        svc = TacticalStrategicAnalyticsService()
        return Response(
            svc.tendencia_temporal(
                distrito=request.query_params.get("zona") or None,
                tipo=request.query_params.get("tipo") or None,
            )
        )


@method_decorator(csrf_exempt, name="dispatch")
class ByZoneView(APIView):
    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        limit = _int(request.query_params.get("limit"), 20)
        return Response(TacticalStrategicAnalyticsService().por_zona(limit=limit))


@method_decorator(csrf_exempt, name="dispatch")
class ByTypeView(APIView):
    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        limit = _int(request.query_params.get("limit"), 20)
        return Response(TacticalStrategicAnalyticsService().por_tipo(limit=limit))


@method_decorator(csrf_exempt, name="dispatch")
class ByStateView(APIView):
    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        ambito = request.query_params.get("ambito") or "expediente"
        return Response(TacticalStrategicAnalyticsService().por_estado(ambito=ambito))


@method_decorator(csrf_exempt, name="dispatch")
class ByUserView(APIView):
    permission_classes = [IsAnalistaCriminalJWT]

    def get(self, request):
        limit = _int(request.query_params.get("limit"), 20)
        return Response(TacticalStrategicAnalyticsService().por_usuario(limit=limit))


@method_decorator(csrf_exempt, name="dispatch")
class ByPatrolView(APIView):
    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        limit = _int(request.query_params.get("limit"), 20)
        return Response(TacticalStrategicAnalyticsService().por_patrulla(limit=limit))


@method_decorator(csrf_exempt, name="dispatch")
class ByEvidenceView(APIView):
    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        return Response(TacticalStrategicAnalyticsService().por_evidencia())


def _int(value, default: int) -> int:
    try:
        return max(1, min(int(value), 1000))
    except (TypeError, ValueError):
        return default
