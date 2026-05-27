from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from packages.autenticacion_seguridad.permissions import _attach_user_from_token

DASHBOARD_ROLES = frozenset({"admin", "comisario", "analista criminal"})
ANALISTA_ROLES = frozenset({"admin", "analista criminal"})


def _role_name(request: Request) -> str:
    user = getattr(request, "crimetrack_user", {})
    return str(user.get("nombre_rol", "")).lower().strip()


class IsDashboardViewerJWT(BasePermission):
    """Comisario, Analista Criminal y Admin."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        return _role_name(request) in DASHBOARD_ROLES


class IsAnalistaCriminalJWT(BasePermission):
    """Indicadores operativos: solo Analista Criminal y Admin."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        return _role_name(request) in ANALISTA_ROLES
