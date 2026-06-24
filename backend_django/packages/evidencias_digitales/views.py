from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAuthenticatedJWT
from packages.evidencias_digitales.services.evidencias_service import (
    ESTADOS_CUSTODIA,
    TRANSICIONES,
    EvidenciasService,
)
from packages.expedientes_criminales.services.expediente_service import ExpedienteService
from packages.shared.audit import audit_request


def _actor(request) -> str:
    u = getattr(request, "crimetrack_user", {}) or {}
    nombre = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()
    return nombre or str(u.get("email") or "Usuario")


def _role(request) -> str:
    user = getattr(request, "crimetrack_user", {}) or {}
    return str(user.get("nombre_rol", "")).lower()


def _can_view(request, evidencia: dict) -> bool:
    """Visualizar/descargar: Comisario/Admin; Detective asignado; Oficial creador.

    Los tres actores del caso de uso (Oficial, Detective, Comisario) pueden
    descargar y reproducir la evidencia de los expedientes a los que acceden.
    """
    user = getattr(request, "crimetrack_user", {}) or {}
    role = _role(request)
    if role in ("admin", "comisario"):
        return True
    svc = ExpedienteService()
    case_number = EvidenciasService().resolve_case_number(evidencia.get("fk_caso"))
    if not case_number:
        return False
    if role == "detective":
        return svc.detective_has_active_assignment(int(user["id_usuario"]), case_number)
    if role == "oficial":
        return svc.is_creator(int(user["id_usuario"]), case_number)
    return False


def _can_manage(request, evidencia: dict) -> bool:
    """Admin/Comisario siempre; Detective solo con asignación activa en el caso."""
    user = getattr(request, "crimetrack_user", {}) or {}
    role = _role(request)
    if role in ("admin", "comisario"):
        return True
    if role != "detective":
        return False
    svc = ExpedienteService()
    case_number = EvidenciasService().resolve_case_number(evidencia.get("fk_caso"))
    if not case_number:
        return False
    return svc.detective_has_active_assignment(int(user["id_usuario"]), case_number)


def _can_delete(request) -> bool:
    """Eliminar evidencia: SOLO Comisario (y Admin como superusuario)."""
    return _role(request) in ("admin", "comisario")


@method_decorator(csrf_exempt, name="dispatch")
class EvidenciaCustodiaOpcionesView(APIView):
    """GET — catálogo de estados de custodia y transiciones permitidas."""

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        return Response(
            {
                "estados": list(ESTADOS_CUSTODIA),
                "transiciones": {k: list(v) for k, v in TRANSICIONES.items()},
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class EvidenciaCustodiaView(APIView):
    """POST — registra una transición de estado en la cadena de custodia (CU-O29)."""

    permission_classes = [IsAuthenticatedJWT]
    parser_classes = [JSONParser]

    def post(self, request, id_evidencia: int):
        svc = EvidenciasService()
        evidencia = svc.get(id_evidencia)
        if not evidencia:
            return Response(
                {"detail": "Evidencia no encontrada"}, status=status.HTTP_404_NOT_FOUND
            )
        if not _can_manage(request, evidencia):
            return Response(
                {"detail": "No autorizado para gestionar la custodia de esta evidencia"},
                status=status.HTTP_403_FORBIDDEN,
            )

        nuevo_estado = str(request.data.get("estado", "")).strip()
        motivo = str(request.data.get("motivo", "")).strip()
        if not nuevo_estado:
            return Response(
                {"detail": "El campo 'estado' es obligatorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            antes, despues = svc.change_custody(
                id_evidencia,
                nuevo_estado=nuevo_estado,
                user=request.crimetrack_user,
                motivo=motivo,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        detalle = (
            f"{_actor(request)} cambió la custodia de la evidencia #{id_evidencia}: "
            f"«{antes.get('estado_custodia')}» → «{despues.get('estado_custodia')}»"
        )
        if motivo:
            detalle += f" — motivo: {motivo}"
        audit_request(
            request,
            accion="EVIDENCE_CUSTODY_CHANGED",
            tabla="app_evidencias",
            detalle=detalle,
            antes=antes,
            despues=despues,
        )
        return Response(despues, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class EvidenciaDescargarView(APIView):
    """GET — descarga/transmite el archivo de la evidencia (Oficial, Detective, Comisario)."""

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request, id_evidencia: int):
        svc = EvidenciasService()
        evidencia = svc.get(id_evidencia)
        if not evidencia:
            return Response(
                {"detail": "Evidencia no encontrada"}, status=status.HTTP_404_NOT_FOUND
            )
        if not _can_view(request, evidencia):
            return Response(
                {"detail": "No autorizado para acceder a esta evidencia"},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            data = svc.download(id_evidencia)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"detail": "No se pudo recuperar el archivo de la evidencia"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        audit_request(
            request,
            accion="EVIDENCE_DOWNLOADED",
            tabla="app_evidencias",
            detalle=(
                f"{_actor(request)} descargó/visualizó la evidencia #{id_evidencia} "
                f"'{data['filename']}'"
            ),
        )
        inline = str(request.query_params.get("inline", "")).lower() in ("1", "true", "yes")
        disp = "inline" if inline else "attachment"
        safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in data["filename"])
        response = HttpResponse(data["body"], content_type=data["content_type"])
        response["Content-Disposition"] = f'{disp}; filename="{safe}"'
        response["Content-Length"] = str(len(data["body"]))
        return response


@method_decorator(csrf_exempt, name="dispatch")
class EvidenciaEliminarView(APIView):
    """DELETE — elimina la evidencia. SOLO Comisario (CU: Eliminar evidencia)."""

    permission_classes = [IsAuthenticatedJWT]

    def delete(self, request, id_evidencia: int):
        if not _can_delete(request):
            return Response(
                {"detail": "Solo el Comisario puede eliminar evidencias."},
                status=status.HTTP_403_FORBIDDEN,
            )
        svc = EvidenciasService()
        try:
            removed = svc.delete(id_evidencia, user=request.crimetrack_user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        audit_request(
            request,
            accion="EVIDENCE_DELETED",
            tabla="app_evidencias",
            detalle=(
                f"{_actor(request)} eliminó la evidencia #{id_evidencia} "
                f"'{removed.get('nombre_archivo')}' (estado de custodia: "
                f"{removed.get('estado_custodia')})"
            ),
            antes=removed,
        )
        return Response({"ok": True, "id_evidencia": id_evidencia}, status=status.HTTP_200_OK)
