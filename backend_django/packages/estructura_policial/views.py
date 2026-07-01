from __future__ import annotations

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAdminJWT, IsAuthenticatedJWT
from packages.estructura_policial.services.organizacion_service import OrganizacionPolicialService
from packages.estructura_policial.services.personal_service import PersonalPolicialService
from packages.estructura_policial.services.seed import seed_estructura_policial
from packages.shared.audit import audit_request


def _err(exc: Exception, code=400):
    return Response({"error": str(exc)}, status=code)


@method_decorator(csrf_exempt, name="dispatch")
class DepartamentosView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        return Response({"items": OrganizacionPolicialService().list_departamentos()})

    def post(self, request):
        if not IsAdminJWT().has_permission(request, self):
            return Response({"error": "Solo administrador"}, status=403)
        try:
            row = OrganizacionPolicialService().create_departamento(request.data or {})
            audit_request(request, accion="DEPTO_CREATED", tabla="app_departamentos_policiales", detalle=row.get("nombre", ""))
            return Response(row, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class DistritosView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        fk = request.query_params.get("fk_departamento")
        fk_int = int(fk) if fk else None
        return Response({"items": OrganizacionPolicialService().list_distritos(fk_departamento=fk_int)})

    def post(self, request):
        if not IsAdminJWT().has_permission(request, self):
            return Response({"error": "Solo administrador"}, status=403)
        try:
            row = OrganizacionPolicialService().create_distrito(request.data or {})
            audit_request(request, accion="DISTRITO_CREATED", tabla="app_distritos_policiales", detalle=row.get("nombre", ""))
            return Response(row, status=status.HTTP_201_CREATED)
        except (ValueError, KeyError) as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class EstacionesView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        fk = request.query_params.get("fk_distrito")
        fk_int = int(fk) if fk else None
        return Response({"items": OrganizacionPolicialService().list_estaciones(fk_distrito=fk_int)})

    def post(self, request):
        if not IsAdminJWT().has_permission(request, self):
            return Response({"error": "Solo administrador"}, status=403)
        try:
            row = OrganizacionPolicialService().create_estacion(request.data or {})
            audit_request(request, accion="ESTACION_CREATED", tabla="app_estaciones_policiales", detalle=row.get("nombre", ""))
            return Response(row, status=status.HTTP_201_CREATED)
        except (ValueError, KeyError) as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class RangosView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        return Response({"items": PersonalPolicialService().list_rangos()})


@method_decorator(csrf_exempt, name="dispatch")
class PersonalPolicialListCreateView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        fk_dist = request.query_params.get("fk_distrito")
        fk_est = request.query_params.get("fk_estacion")
        return Response(
            {
                "items": PersonalPolicialService().list_personal(
                    fk_distrito=int(fk_dist) if fk_dist else None,
                    fk_estacion=int(fk_est) if fk_est else None,
                )
            }
        )

    def post(self, request):
        try:
            row = PersonalPolicialService().create_personal(request.data or {})
            audit_request(
                request,
                accion="PERSONAL_CREATED",
                tabla="app_personal_policial",
                detalle=f"{row.get('nombres')} {row.get('apellidos')} ({row.get('numero_placa')})",
            )
            return Response(row, status=status.HTTP_201_CREATED)
        except (ValueError, KeyError) as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class PersonalPolicialDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, id_personal: int):
        row = PersonalPolicialService().update_personal(id_personal, request.data or {})
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        audit_request(request, accion="PERSONAL_UPDATED", tabla="app_personal_policial", detalle=f"id={id_personal}")
        return Response(row)


@method_decorator(csrf_exempt, name="dispatch")
class SeedEstructuraView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if not settings.DEBUG:
            return Response({"error": "Solo en DEBUG"}, status=403)
        result = seed_estructura_policial(reset=bool(request.data.get("reset", False)))
        return Response(result)
