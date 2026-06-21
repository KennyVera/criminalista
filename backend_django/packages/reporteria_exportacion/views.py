from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.reporteria_exportacion.permissions import CanManageReportsJWT
from packages.reporteria_exportacion.services.report_service import (
    FRECUENCIAS,
    TIPOS_REPORTE,
    ReportService,
)
from packages.shared.audit import audit_request


def _actor(request) -> str:
    u = getattr(request, "crimetrack_user", {}) or {}
    nombre = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()
    return nombre or str(u.get("email") or "Usuario")


def _err(exc: Exception, code=400):
    return Response({"error": str(exc)}, status=code)


def _svc() -> ReportService:
    return ReportService()


@method_decorator(csrf_exempt, name="dispatch")
class ReportOptionsView(APIView):
    """GET — catálogos para la UI (tipos de reporte, frecuencias)."""

    permission_classes = [CanManageReportsJWT]

    def get(self, request):
        return Response(
            {
                "tipos_reporte": [{"value": k, "label": v} for k, v in TIPOS_REPORTE.items()],
                "frecuencias": list(FRECUENCIAS),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ReportSendView(APIView):
    """POST — CU-O40: enviar un reporte por correo al destinatario indicado."""

    permission_classes = [CanManageReportsJWT]

    def post(self, request):
        data = request.data or {}
        try:
            result = _svc().send_report(
                tipo_reporte=str(data.get("tipo_reporte") or "operativo"),
                destinatarios=data.get("destinatarios"),
                case_number=data.get("case_number") or None,
                generado_por=_actor(request),
                mensaje=str(data.get("mensaje") or ""),
            )
        except ValueError as exc:
            return _err(exc)
        except Exception as exc:  # noqa: BLE001
            return _err(exc, 502)

        audit_request(
            request,
            accion="REPORT_SENT",
            tabla="sys_reportes_programados",
            detalle=(
                f"{_actor(request)} envió el reporte '{result['tipo_reporte']}' "
                f"a {', '.join(result['destinatarios'])}"
            ),
            despues=result,
        )
        return Response(result, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class ReportScheduleListView(APIView):
    """GET lista / POST crea programaciones (CU-O38)."""

    permission_classes = [CanManageReportsJWT]

    def get(self, request):
        return Response({"items": _svc().list_schedules()})

    def post(self, request):
        data = request.data or {}
        try:
            row = _svc().create_schedule(
                nombre=str(data.get("nombre") or ""),
                tipo_reporte=str(data.get("tipo_reporte") or "operativo"),
                destinatarios=data.get("destinatarios"),
                frecuencia=str(data.get("frecuencia") or ""),
                hora_programada=str(data.get("hora_programada") or "08:00"),
                creado_por=_actor(request),
                activo=bool(data.get("activo", True)),
            )
        except ValueError as exc:
            return _err(exc)

        audit_request(
            request,
            accion="REPORT_SCHEDULE_CREATED",
            tabla="sys_reportes_programados",
            detalle=(
                f"{_actor(request)} programó el reporte '{row['nombre']}' "
                f"({row['frecuencia']} a las {row['hora_programada']})"
            ),
            despues=row,
        )
        return Response(row, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class ReportScheduleDetailView(APIView):
    """PATCH actualiza / DELETE elimina una programación."""

    permission_classes = [CanManageReportsJWT]

    def patch(self, request, schedule_id: int):
        try:
            row = _svc().update_schedule(int(schedule_id), request.data or {})
        except ValueError as exc:
            return _err(exc)
        if not row:
            return _err(ValueError("Programación no encontrada"), 404)
        audit_request(
            request,
            accion="REPORT_SCHEDULE_UPDATED",
            tabla="sys_reportes_programados",
            detalle=f"{_actor(request)} actualizó la programación de reporte #{schedule_id}",
            despues=row,
        )
        return Response(row)

    def delete(self, request, schedule_id: int):
        ok = _svc().delete_schedule(int(schedule_id))
        if not ok:
            return _err(ValueError("Programación no encontrada"), 404)
        audit_request(
            request,
            accion="REPORT_SCHEDULE_DELETED",
            tabla="sys_reportes_programados",
            detalle=f"{_actor(request)} eliminó la programación de reporte #{schedule_id}",
        )
        return Response({"deleted": True})
