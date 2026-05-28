"""Permisos para operador de recuperación (JWT recovery_mode)."""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from packages.autenticacion_seguridad.permissions import _attach_user_from_token
from packages.autenticacion_seguridad.services.jwt_tokens import decode_access_token


class IsRecoveryOperatorJWT(BasePermission):
    """Token de recuperación o Admin con sesión normal."""

    def has_permission(self, request: Request, view) -> bool:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False
        token = auth[7:].strip()
        try:
            payload = decode_access_token(token)
        except Exception:
            return False
        if payload.get("recovery_mode"):
            request.crimetrack_recovery = True  # type: ignore[attr-defined]
            request.crimetrack_user = {
                "id_usuario": 0,
                "email": payload.get("email", ""),
                "nombre_rol": "Admin",
                "recovery_mode": True,
            }
            return True
        return _attach_user_from_token(request) and str(
            getattr(request, "crimetrack_user", {}).get("nombre_rol", "")
        ).lower() == "admin"
