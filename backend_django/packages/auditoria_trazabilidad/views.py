from __future__ import annotations

from datetime import datetime, timezone

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAdminJWT
from packages.auditoria_trazabilidad.services.audit_query import AuditQueryService
from packages.shared.audit import audit_request


def _filters(request) -> dict:
    qp = request.query_params
    return {
        "q": qp.get("q", ""),
        "accion": qp.get("accion", ""),
        "categoria": qp.get("categoria", ""),
        "operacion": qp.get("operacion", ""),
        "severidad": qp.get("severidad", ""),
        "resultado": qp.get("resultado", ""),
        "ip": qp.get("ip", ""),
        "fk_usuario": qp.get("fk_usuario", ""),
        "desde": qp.get("desde", ""),
        "hasta": qp.get("hasta", ""),
    }


@method_decorator(csrf_exempt, name="dispatch")
class AuditEventsView(APIView):
    """GET — eventos de auditoría con filtros, paginación y estadísticas (solo Admin)."""

    permission_classes = [IsAdminJWT]

    def get(self, request):
        try:
            page = int(request.query_params.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = int(request.query_params.get("per_page", 15))
        except (TypeError, ValueError):
            per_page = 15
        data = AuditQueryService().query(_filters(request), page=page, per_page=per_page)
        return Response(data)


@method_decorator(csrf_exempt, name="dispatch")
class AuditExportView(APIView):
    """GET — exportación CSV autorizada y auditada de los eventos filtrados (CU-O13/O74)."""

    permission_classes = [IsAdminJWT]

    def get(self, request):
        filters = _filters(request)
        csv_bytes = AuditQueryService().export_csv(filters)
        # La exportación queda auditada (RN-08).
        audit_request(
            request,
            accion="AUDIT_EXPORTED",
            tabla="app_audit_logs",
            detalle=f"Exportación CSV de auditoría · filtros={filters}",
        )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="auditoria_{stamp}.csv"'
        response["Content-Length"] = str(len(csv_bytes))
        return response
