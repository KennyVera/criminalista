from __future__ import annotations

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


def _can_manage(request, evidencia: dict) -> bool:
    """Admin/Comisario siempre; Detective solo con asignación activa en el caso."""
    user = getattr(request, "crimetrack_user", {}) or {}
    role = str(user.get("nombre_rol", "")).lower()
    if role in ("admin", "comisario"):
        return True
    if role != "detective":
        return False
    svc = ExpedienteService()
    try:
        dim = svc.olap.get_record("dim_caso", str(int(evidencia.get("fk_caso"))))
    except Exception:
        dim = None
    case_number = str((dim or {}).get("case_number") or "")
    if not case_number:
        return False
    return svc.detective_has_active_assignment(int(user["id_usuario"]), case_number)


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
