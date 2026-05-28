from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.administracion_sistema.recovery_permissions import IsRecoveryOperatorJWT
from packages.administracion_sistema.services.restore_pipeline import (
    get_restore_progress,
    request_cancel_restore,
)
from packages.autenticacion_seguridad.permissions import IsAdminJWT


@method_decorator(csrf_exempt, name="dispatch")
class RestoreEtlStatusView(APIView):
    """GET progreso restauración + ETL."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, task_id: str):
        return Response(get_restore_progress(task_id))


@method_decorator(csrf_exempt, name="dispatch")
class RestoreEtlStatusAdminView(RestoreEtlStatusView):
    permission_classes = [IsAdminJWT]


@method_decorator(csrf_exempt, name="dispatch")
class RestoreEtlStatusRecoveryView(RestoreEtlStatusView):
    permission_classes = [IsRecoveryOperatorJWT]


@method_decorator(csrf_exempt, name="dispatch")
class RestoreEtlCancelView(APIView):
    """POST — solicita cancelar restauración + ETL y revertir datos."""

    authentication_classes = []
    permission_classes = []

    def post(self, request, task_id: str):
        return Response(request_cancel_restore(task_id))


@method_decorator(csrf_exempt, name="dispatch")
class RestoreEtlCancelAdminView(RestoreEtlCancelView):
    permission_classes = [IsAdminJWT]


@method_decorator(csrf_exempt, name="dispatch")
class RestoreEtlCancelRecoveryView(RestoreEtlCancelView):
    permission_classes = [IsRecoveryOperatorJWT]
