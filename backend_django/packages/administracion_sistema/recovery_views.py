from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.administracion_sistema.recovery_permissions import IsRecoveryOperatorJWT
from packages.administracion_sistema.services.backups_admin import BackupsAdminService
from packages.administracion_sistema.services.recovery_service import RecoveryService
from packages.administracion_sistema.services.restore_pipeline import enqueue_restore_and_etl


def _err(exc: Exception, code: int = 400) -> Response:
    return Response({"error": str(exc)}, status=code)


@method_decorator(csrf_exempt, name="dispatch")
class RecoveryStatusView(APIView):
    """GET público — ¿el sistema necesita restauración?"""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(RecoveryService().check_status())


@method_decorator(csrf_exempt, name="dispatch")
class RecoveryLoginView(APIView):
    """POST público — login de emergencia (solo si recovery_required)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        if not email or not password:
            return Response(
                {"error": "email y password son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return Response(RecoveryService().recovery_login(email, password))
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class RecoveryHistorialView(APIView):
    permission_classes = [IsRecoveryOperatorJWT]

    def get(self, request):
        return Response({"items": RecoveryService().list_historial_recovery()})


@method_decorator(csrf_exempt, name="dispatch")
class RecoveryRestaurarView(APIView):
    permission_classes = [IsRecoveryOperatorJWT]

    def post(self, request):
        upload = request.FILES.get("archivo")
        if not upload:
            return Response(
                {"error": "Envía el archivo ZIP en el campo 'archivo'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = getattr(request, "crimetrack_user", {})
        operador = user.get("email") or "recovery_admin"
        try:
            task_id = enqueue_restore_and_etl(
                upload.read(),
                ejecutado_por=operador,
                export_raw_copy=False,
            )
            return Response(
                {
                    "task_id": task_id,
                    "status": "running",
                    "message": "Restauración y ETL en curso. Consulte el progreso.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as exc:
            return _err(exc, 500)


@method_decorator(csrf_exempt, name="dispatch")
class RecoveryDescargarView(APIView):
    permission_classes = [IsRecoveryOperatorJWT]

    def get(self, request, historial_id: int):
        try:
            data, filename = BackupsAdminService().build_download_zip(historial_id)
            response = HttpResponse(data, content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except ValueError as exc:
            return _err(exc)
        except Exception as exc:
            return _err(exc, 500)
