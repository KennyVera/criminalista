from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.dashboard_analitica.permissions import IsAnalistaCriminalJWT, IsDashboardViewerJWT
from packages.dashboard_analitica.services.dashboard_service import DashboardService
from packages.dashboard_analitica.services.direct_access_service import DashboardDirectAccessService


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
class DashboardDirectAccessManifestView(APIView):
    """
    GET — JSON ligero con Presigned URLs Parquet (Direct-to-Client).
    React + DuckDB-Wasm consumen MinIO sin pasar por serialización Django.
    """

    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        try:
            expires = request.query_params.get("expires_in")
            ttl = int(expires) if expires and expires.isdigit() else None
            return Response(DashboardDirectAccessService().manifest(expires_in=ttl))
        except Exception as exc:
            return _minio_error(exc)


@method_decorator(csrf_exempt, name="dispatch")
class DashboardDirectAccessPreviewView(APIView):
    """GET — agregación pushdown en servidor (máx. 500 filas para UI)."""

    permission_classes = [IsDashboardViewerJWT]

    def get(self, request):
        limit_raw = request.query_params.get("limit", "500")
        try:
            limit = max(1, min(int(limit_raw), 5000))
        except ValueError:
            limit = 500
        try:
            data = DashboardDirectAccessService().server_side_preview(
                distrito=request.query_params.get("zona") or None,
                tipo=request.query_params.get("tipo") or None,
                year=request.query_params.get("anio") or None,
                month=request.query_params.get("mes") or None,
                limit=limit,
            )
            return Response(data)
        except Exception:
            from packages.dashboard_analitica.services.dashboard_service import DashboardService

            fallback = DashboardService().filtered_stats(
                distrito=request.query_params.get("zona") or None,
                tipo=request.query_params.get("tipo") or None,
                year=request.query_params.get("anio") or None,
                month=request.query_params.get("mes") or None,
            )
            rows = []
            for item in fallback.get("por_distrito") or []:
                rows.append(
                    {
                        "distrito": item.get("district"),
                        "beat": item.get("beat"),
                        "tipo": "",
                        "anio": "",
                        "mes": "",
                        "total": item.get("total_crimes"),
                    }
                )
            return Response(
                {
                    "rows": rows[:limit],
                    "total_hechos": int(fallback.get("total_hechos") or 0),
                    "query_ms": 0,
                    "source": "materialized_fallback",
                }
            )


@method_decorator(csrf_exempt, name="dispatch")
class DashboardCrimeForecastView(APIView):
    """CU-O20 — predicción/pronóstico de incidencia criminal (solo Analista Criminal / Admin)."""

    permission_classes = [IsAnalistaCriminalJWT]

    def get(self, request):
        try:
            horizon_raw = request.query_params.get("horizonte", "6")
            try:
                horizon = int(horizon_raw)
            except ValueError:
                horizon = 6
            data = DashboardService().crime_forecast(
                horizon=horizon,
                distrito=request.query_params.get("zona") or None,
                tipo=request.query_params.get("tipo") or None,
            )
            return Response(data)
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
