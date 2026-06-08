from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.asignacion_investigaciones.permissions import (
    IsComisarioJWT,
    IsComisarioOrDetectiveJWT,
)
from packages.asignacion_investigaciones.services.assignment_service import AssignmentService


def _err(exc: Exception, code=400):
    return Response({"error": str(exc)}, status=code)


@method_decorator(csrf_exempt, name="dispatch")
class DetectivesDisponiblesView(APIView):
    """GET — HU-2: detectives y carga laboral."""

    permission_classes = [IsComisarioJWT]

    def get(self, request):
        return Response({"items": AssignmentService().list_detectives_workload()})


@method_decorator(csrf_exempt, name="dispatch")
class CasosAsignacionView(APIView):
    """GET — casos para asignar (opcional ?sin_asignar=1)."""

    permission_classes = [IsComisarioJWT]

    def get(self, request):
        solo = request.query_params.get("sin_asignar") in ("1", "true", "yes")
        solo_asignados = request.query_params.get("asignados") in ("1", "true", "yes")
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            per_page = max(1, min(int(request.query_params.get("per_page", 40)), 100))
        except ValueError:
            page, per_page = 1, 40
        q = str(request.query_params.get("q", "")).strip()
        estado = str(request.query_params.get("estado", "")).strip()
        prioridad = str(request.query_params.get("prioridad", "")).strip()
        if solo_asignados:
            solo = False
        return Response(
            AssignmentService().list_casos(
                q=q,
                page=page,
                per_page=per_page,
                solo_sin_asignar=solo,
                solo_asignados=solo_asignados,
                estado=estado,
                prioridad=prioridad,
            )
        )


@method_decorator(csrf_exempt, name="dispatch")
class AsignarDetectiveView(APIView):
    """POST — HU-1/3: asignar detective a caso."""

    permission_classes = [IsComisarioJWT]

    def post(self, request):
        user = request.crimetrack_user
        fk_caso = request.data.get("fk_caso")
        fk_detective = request.data.get("fk_detective")
        if not fk_caso or not fk_detective:
            return _err(ValueError("fk_caso y fk_detective son obligatorios"))
        try:
            result = AssignmentService().assign_detective(
                fk_caso=int(fk_caso),
                fk_detective=int(fk_detective),
                comisario=user,
                observaciones=str(request.data.get("observaciones", "")),
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ReasignarDetectiveView(APIView):
    """POST — HU-4: reasignar detective."""

    permission_classes = [IsComisarioJWT]

    def post(self, request, fk_caso: int):
        user = request.crimetrack_user
        fk_detective = request.data.get("fk_detective")
        if not fk_detective:
            return _err(ValueError("fk_detective es obligatorio"))
        try:
            result = AssignmentService().reassign_detective(
                fk_caso=fk_caso,
                fk_detective=int(fk_detective),
                comisario=user,
                observaciones=str(request.data.get("observaciones", "")),
            )
            return Response(result)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class RemoverDetectiveView(APIView):
    """POST — HU-4: remover detective del caso."""

    permission_classes = [IsComisarioJWT]

    def post(self, request, fk_caso: int):
        user = request.crimetrack_user
        try:
            result = AssignmentService().remove_detective(
                fk_caso=fk_caso,
                comisario=user,
                motivo=str(request.data.get("motivo", "")),
            )
            return Response(result)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ProgresoInvestigacionView(APIView):
    """GET — expedientes asignados y avance (Comisario ve todos; Detective solo los suyos)."""

    permission_classes = [IsComisarioOrDetectiveJWT]

    def get(self, request):
        user = request.crimetrack_user
        role = str(user.get("nombre_rol", "")).lower()
        solo = role == "detective" or request.query_params.get("mis_casos") in (
            "1",
            "true",
        )
        return Response(
            AssignmentService().investigation_progress(user=user, solo_mis_casos=solo)
        )
