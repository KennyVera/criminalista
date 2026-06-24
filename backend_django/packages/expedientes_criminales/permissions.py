from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from packages.autenticacion_seguridad.permissions import _attach_user_from_token
from packages.expedientes_criminales.services.expediente_service import ExpedienteService


def _role(request: Request) -> str:
    user = getattr(request, "crimetrack_user", {}) or {}
    return str(user.get("nombre_rol", "")).lower()


def _case_number(request: Request, view) -> str | None:
    return view.kwargs.get("case_number") or request.parser_context.get(
        "kwargs", {}
    ).get("case_number")


class CanAccessExpedienteJWT(BasePermission):
    """Comisario/Admin siempre; Detective con asignación activa.

    El Oficial puede CONSULTAR cualquier expediente (la lista es unificada con
    los casos), pero solo puede ESCRIBIR (involucrados/evidencias preliminares)
    sobre los expedientes que él mismo registró.
    """

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        user = getattr(request, "crimetrack_user", {})
        case_number = _case_number(request, view)
        if not case_number:
            return False
        role = _role(request)
        if role in ("admin", "comisario"):
            return True
        svc = ExpedienteService()
        if role == "detective":
            # El Detective solo accede (consulta detalle, agrega involucrados,
            # evidencias y progreso) a los expedientes que el Comisario le asignó.
            # La lista unificada la puede ver completa (CanListExpedientesJWT),
            # pero el detalle exige asignación activa.
            return svc.detective_has_active_assignment(
                int(user["id_usuario"]),
                case_number,
            )
        if role == "oficial":
            # Puede consultar cualquier expediente, pero solo aporta
            # involucrados/evidencias preliminares en los que él registró.
            if request.method in SAFE_METHODS:
                return True
            return svc.is_creator(int(user["id_usuario"]), case_number)
        return False


class CanManageBitacoraJWT(BasePermission):
    """Avances de investigación: Detective asignado, Comisario o Admin.

    El Oficial NO registra progresos; solo hace el registro inicial del hecho.
    """

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        user = getattr(request, "crimetrack_user", {})
        case_number = _case_number(request, view)
        if not case_number:
            return False
        role = _role(request)
        if role in ("admin", "comisario"):
            return True
        if role == "detective":
            return ExpedienteService().detective_has_active_assignment(
                int(user["id_usuario"]),
                case_number,
            )
        return False


class CanListExpedientesJWT(BasePermission):
    """Consulta del listado de expedientes para roles operativos."""

    allowed = ("admin", "comisario", "detective", "oficial")

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        return _role(request) in self.allowed


class CanRegisterExpedienteJWT(BasePermission):
    """Registrar nuevos expedientes: Oficial (principal), Comisario y Admin."""

    allowed = ("oficial", "comisario", "admin")

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        return _role(request) in self.allowed


class CanEditExpedienteJWT(BasePermission):
    """Editar / cerrar: Detective asignado, Comisario o Admin."""

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        user = getattr(request, "crimetrack_user", {})
        case_number = _case_number(request, view)
        if not case_number:
            return False
        role = _role(request)
        if role in ("admin", "comisario"):
            return True
        if role == "detective":
            return ExpedienteService().detective_has_active_assignment(
                int(user["id_usuario"]),
                case_number,
            )
        return False


class CanManageExpedienteLifecycleJWT(BasePermission):
    """Reabrir, archivar y autorizar eliminación lógica: solo Comisario/Admin."""

    allowed = ("comisario", "admin")

    def has_permission(self, request: Request, view) -> bool:
        if not _attach_user_from_token(request):
            return False
        return _role(request) in self.allowed
