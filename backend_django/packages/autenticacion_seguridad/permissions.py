from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from packages.autenticacion_seguridad.services.auth_service import AuthError, AuthService


def _attach_user_from_token(request: Request) -> bool:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth[7:].strip()
    try:
        request.crimetrack_user = AuthService().me_from_token(token)  # type: ignore[attr-defined]
        request.crimetrack_token = token  # type: ignore[attr-defined]
        return True
    except AuthError as exc:
        request.auth_error = exc  # type: ignore[attr-defined]
        return False


class IsAuthenticatedJWT(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return _attach_user_from_token(request)


class IsAdminJWT(BasePermission):
    """Solo rol Admin (gestionar sesiones activas, etc.)."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        user = getattr(request, "crimetrack_user", {})
        return str(user.get("nombre_rol", "")).lower() == "admin"
