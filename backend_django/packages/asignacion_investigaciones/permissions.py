from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from packages.autenticacion_seguridad.permissions import _attach_user_from_token


class IsComisarioJWT(BasePermission):
    """Comisario o Admin — gestionar asignaciones."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        role = str(getattr(request, "crimetrack_user", {}).get("nombre_rol", "")).lower()
        return role in ("comisario", "admin")


class IsComisarioOrDetectiveJWT(BasePermission):
    """Comisario, Detective o Admin — consultar progreso."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        role = str(getattr(request, "crimetrack_user", {}).get("nombre_rol", "")).lower()
        return role in ("comisario", "detective", "admin")


class IsDespachoJWT(BasePermission):
    """Despacho/Operaciones de patrulla: Comisario, Oficial (operador) o Admin."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        role = str(getattr(request, "crimetrack_user", {}).get("nombre_rol", "")).lower()
        return role in ("comisario", "oficial", "admin")


class IsOficialJWT(BasePermission):
    """Vista del oficial receptor: Oficial (o Comisario/Admin para supervisión)."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        role = str(getattr(request, "crimetrack_user", {}).get("nombre_rol", "")).lower()
        return role in ("oficial", "comisario", "admin")
