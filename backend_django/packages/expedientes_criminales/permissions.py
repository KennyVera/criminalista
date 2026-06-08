from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from packages.autenticacion_seguridad.permissions import _attach_user_from_token
from packages.expedientes_criminales.services.expediente_service import ExpedienteService


class CanAccessExpedienteJWT(BasePermission):
    """Detective solo si tiene asignación activa; Comisario/Admin siempre."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        user = getattr(request, "crimetrack_user", {})
        case_number = view.kwargs.get("case_number") or request.parser_context.get(
            "kwargs", {}
        ).get("case_number")
        if not case_number:
            return False
        role = str(user.get("nombre_rol", "")).lower()
        if role in ("admin", "comisario"):
            return True
        if role == "detective":
            return ExpedienteService().detective_has_active_assignment(
                int(user["id_usuario"]),
                case_number,
            )
        return False
