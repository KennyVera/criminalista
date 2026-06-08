from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.expedientes_criminales.permissions import CanAccessExpedienteJWT
from packages.expedientes_criminales.services.expediente_service import ExpedienteService
from packages.expedientes_criminales.services.informe_pdf_ecuador import build_informe_pdf


def _err(exc: Exception, code=400):
    return Response({"error": str(exc)}, status=code)


def _svc() -> ExpedienteService:
    return ExpedienteService()


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteCabeceraView(APIView):
    permission_classes = [CanAccessExpedienteJWT]

    def get(self, request, case_number: str):
        try:
            return Response(_svc().get_cabecera(case_number))
        except Exception as exc:
            return _err(exc, 500)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteDetallesGeneralesView(APIView):
    """Tab 1 — Data Lake MinIO crimes_220k."""

    permission_classes = [CanAccessExpedienteJWT]

    def get(self, request, case_number: str):
        return Response(_svc().detalles_generales(case_number))


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteInvolucradosView(APIView):
    permission_classes = [CanAccessExpedienteJWT]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request, case_number: str):
        return Response({"items": _svc().list_involucrados(case_number)})

    def post(self, request, case_number: str):
        try:
            row = _svc().add_involucrado(
                case_number,
                user=request.crimetrack_user,
                data=request.data,
            )
            return Response(row, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteEvidenciasView(APIView):
    permission_classes = [CanAccessExpedienteJWT]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, case_number: str):
        return Response({"items": _svc().list_evidencias(case_number)})

    def post(self, request, case_number: str):
        archivo = request.FILES.get("archivo")
        if not archivo:
            return _err(ValueError("Campo 'archivo' requerido (multipart)"))
        try:
            row = _svc().upload_evidencia(
                case_number,
                user=request.crimetrack_user,
                file_obj=archivo,
                filename=archivo.name,
                tipo_evidencia=str(request.data.get("tipo_evidencia", "Multimedia")),
            )
            return Response(row, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteBitacoraView(APIView):
    permission_classes = [CanAccessExpedienteJWT]
    parser_classes = [JSONParser]

    def get(self, request, case_number: str):
        return Response({"items": _svc().list_bitacora(case_number)})

    def post(self, request, case_number: str):
        nota = str(request.data.get("nota", "")).strip()
        if not nota:
            return _err(ValueError("La nota es obligatoria"))
        try:
            avance = int(request.data.get("avance_pct", 0))
            estado = str(request.data.get("estado_caso", "En investigación"))
            row = _svc().add_bitacora_entry(
                case_number,
                user=request.crimetrack_user,
                nota=nota,
                avance_pct=avance,
                estado_caso=estado,
            )
            return Response(row, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteInformePdfView(APIView):
    """GET — informe PDF formato Ecuador (hecho, involucrados, evidencias, bitácora)."""

    permission_classes = [CanAccessExpedienteJWT]

    def get(self, request, case_number: str):
        try:
            user = getattr(request, "crimetrack_user", None)
            pdf_bytes = build_informe_pdf(case_number, user=user)
        except Exception as exc:
            return _err(exc, 500)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_number)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="Informe_Penal_{safe_name}.pdf"'
        )
        return response
