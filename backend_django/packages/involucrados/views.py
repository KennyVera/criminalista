from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAuthenticatedJWT
from packages.involucrados.services.involucrados_service import InvolucradosService
from packages.shared.audit import audit_request

ROLES_LECTURA = ("admin", "comisario", "detective", "oficial", "analista_criminal")
ROLES_ESCRITURA = ("admin", "comisario", "detective", "oficial")


def _actor(request) -> str:
    u = getattr(request, "crimetrack_user", {}) or {}
    nombre = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()
    return nombre or str(u.get("email") or "Usuario")


def _role(request) -> str:
    u = getattr(request, "crimetrack_user", {}) or {}
    return str(u.get("nombre_rol", "")).lower()


def _nombre(persona: dict) -> str:
    return f"{persona.get('nombres', '')} {persona.get('apellidos', '')}".strip() or "s/n"


@method_decorator(csrf_exempt, name="dispatch")
class InvolucradoBuscarView(APIView):
    """GET — busca involucrados por nombre, identificación o alias (CU: Buscar involucrado)."""

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        if _role(request) not in ROLES_LECTURA:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        q = request.query_params.get("q", "")
        try:
            limit = int(request.query_params.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        items = InvolucradosService().search(q, limit=limit)
        return Response({"items": items})


@method_decorator(csrf_exempt, name="dispatch")
class InvolucradoPerfilView(APIView):
    """GET — perfil completo: datos personales, historial criminal y expedientes."""

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request, id_involucrado: int):
        if _role(request) not in ROLES_LECTURA:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        try:
            perfil = InvolucradosService().get_perfil(id_involucrado)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(perfil)


@method_decorator(csrf_exempt, name="dispatch")
class InvolucradoEditarView(APIView):
    """PATCH — edita los datos del involucrado (CU: Editar involucrado)."""

    permission_classes = [IsAuthenticatedJWT]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def patch(self, request, id_involucrado: int):
        if _role(request) not in ROLES_ESCRITURA:
            return Response(
                {"detail": "No autorizado para editar involucrados"},
                status=status.HTTP_403_FORBIDDEN,
            )
        svc = InvolucradosService()
        try:
            antes, despues = svc.update(
                id_involucrado, data=request.data, user=request.crimetrack_user
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        audit_request(
            request,
            accion="INVOLUCRADO_UPDATED",
            tabla="app_involucrados",
            detalle=f"{_actor(request)} editó el perfil del involucrado {_nombre(despues)} (#{id_involucrado})",
            antes=antes,
            despues=despues,
        )
        return Response(despues, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class InvolucradoFotoView(APIView):
    """GET — sirve la foto de perfil. POST — sube/actualiza la foto de perfil."""

    permission_classes = [IsAuthenticatedJWT]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, id_involucrado: int):
        if _role(request) not in ROLES_LECTURA:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        try:
            foto = InvolucradosService().get_foto(id_involucrado)
        except Exception:
            foto = None
        if not foto:
            return Response(
                {"detail": "Sin foto de perfil"}, status=status.HTTP_404_NOT_FOUND
            )
        response = HttpResponse(foto["body"], content_type=foto["content_type"])
        response["Cache-Control"] = "private, max-age=60"
        return response

    def post(self, request, id_involucrado: int):
        if _role(request) not in ROLES_ESCRITURA:
            return Response(
                {"detail": "No autorizado para modificar la foto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        archivo = request.FILES.get("foto") or request.FILES.get("archivo")
        if not archivo:
            return Response(
                {"detail": "Campo 'foto' requerido (multipart)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        svc = InvolucradosService()
        try:
            persona = svc.set_foto(
                id_involucrado,
                file_obj=archivo,
                filename=archivo.name,
                user=request.crimetrack_user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        audit_request(
            request,
            accion="INVOLUCRADO_PHOTO_UPDATED",
            tabla="app_involucrados",
            detalle=f"{_actor(request)} actualizó la foto del involucrado {_nombre(persona)} (#{id_involucrado})",
        )
        return Response(persona, status=status.HTTP_200_OK)
