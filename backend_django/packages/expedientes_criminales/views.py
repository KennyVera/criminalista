from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.cache.redis_cache import cache_response
from packages.expedientes_criminales.permissions import (
    CanAccessExpedienteJWT,
    CanEditExpedienteJWT,
    CanListExpedientesJWT,
    CanManageBitacoraJWT,
    CanManageExpedienteLifecycleJWT,
    CanRegisterExpedienteJWT,
)
from packages.expedientes_criminales.services.expediente_service import ExpedienteService
from packages.expedientes_criminales.services.informe_pdf_ecuador import build_informe_pdf
from packages.shared.audit import audit_request


def _actor(request) -> str:
    u = getattr(request, "crimetrack_user", {}) or {}
    nombre = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()
    return nombre or str(u.get("email") or "Usuario")


def _expediente_case_key(request, *args, **kwargs) -> str:
    return str(kwargs.get("case_number") or (args[0] if args else request.path))


def _err(exc: Exception, code=400):
    return Response({"error": str(exc)}, status=code)


def _svc() -> ExpedienteService:
    return ExpedienteService()


@method_decorator(csrf_exempt, name="dispatch")
class ExpedientesListView(APIView):
    """GET — listado/búsqueda paginada de expedientes. POST — registrar nuevo (Oficial)."""

    parser_classes = [JSONParser, FormParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [CanRegisterExpedienteJWT()]
        return [CanListExpedientesJWT()]

    def get(self, request):
        try:
            return Response(
                _svc().search_expedientes(
                    q=request.query_params.get("q", ""),
                    estado=request.query_params.get("estado", ""),
                    page=int(request.query_params.get("page", 1) or 1),
                    per_page=int(request.query_params.get("per_page", 10) or 10),
                )
            )
        except Exception as exc:
            return _err(exc, 500)

    def post(self, request):
        try:
            row = _svc().register_expediente(user=request.crimetrack_user, data=request.data)
            audit_request(
                request,
                accion="EXPEDIENTE_CREATED",
                tabla="app_expedientes",
                detalle=(
                    f"{_actor(request)} registró el expediente {row.get('case_number')} "
                    f"«{row.get('titulo')}» ({row.get('tipo_delito')}) — estado ACTIVO"
                ),
                despues=row,
            )
            return Response(row, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)
        except Exception as exc:
            return _err(exc, 500)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteCatalogosView(APIView):
    """GET — catálogos para formularios (distritos del sistema, tipos, prioridades)."""

    permission_classes = [CanListExpedientesJWT]

    def get(self, request):
        return Response(_svc().catalogos())


@method_decorator(csrf_exempt, name="dispatch")
class IncidentesDisponiblesView(APIView):
    """GET — busca incidentes (por código, fecha o lugar) para vincular a un expediente."""

    permission_classes = [CanListExpedientesJWT]

    def get(self, request):
        solo_disp = str(request.query_params.get("solo_disponibles", "1")).lower() not in (
            "0",
            "false",
            "no",
        )
        return Response(
            {
                "items": _svc().buscar_incidentes(
                    q=request.query_params.get("q", ""),
                    solo_disponibles=solo_disp,
                    excluir_case=request.query_params.get("excluir_case", ""),
                    limit=int(request.query_params.get("limit", 20) or 20),
                )
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteIncidentesView(APIView):
    """GET — incidentes vinculados a un expediente."""

    permission_classes = [CanAccessExpedienteJWT]

    def get(self, request, case_number: str):
        return Response({"items": _svc().incidentes_de_expediente(case_number)})


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteDuplicadosView(APIView):
    """GET — sugiere expedientes duplicados/similares antes de registrar."""

    permission_classes = [CanRegisterExpedienteJWT]

    def get(self, request):
        return Response(
            {
                "items": _svc().find_similar(
                    case_number=request.query_params.get("case_number", ""),
                    titulo=request.query_params.get("titulo", ""),
                )
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteEditarView(APIView):
    """PATCH — editar datos del expediente (Detective asignado / Comisario)."""

    permission_classes = [CanEditExpedienteJWT]
    parser_classes = [JSONParser, FormParser]

    def patch(self, request, case_number: str):
        try:
            result = _svc().update_expediente(
                case_number, user=request.crimetrack_user, data=request.data
            )
            cambios = ", ".join(result["despues"].keys())
            audit_request(
                request,
                accion="EXPEDIENTE_UPDATED",
                tabla="app_expedientes",
                detalle=(
                    f"{_actor(request)} editó el expediente {case_number} "
                    f"(campos: {cambios})"
                ),
                antes=result["antes"],
                despues=result["despues"],
            )
            return Response(result)
        except ValueError as exc:
            return _err(exc)
        except Exception as exc:
            return _err(exc, 500)


_ESTADO_ACCION_META = {
    "cerrar": ("EXPEDIENTE_CLOSED", "cerró"),
    "reabrir": ("EXPEDIENTE_REOPENED", "reabrió"),
    "archivar": ("EXPEDIENTE_ARCHIVED", "archivó"),
    "eliminar": ("EXPEDIENTE_DELETED", "eliminó lógicamente"),
}


def _audit_estado(request, case_number: str, accion: str, result: dict):
    meta = _ESTADO_ACCION_META.get(accion, ("EXPEDIENTE_STATE_CHANGED", "cambió el estado de"))
    audit_request(
        request,
        accion=meta[0],
        tabla="app_expedientes",
        detalle=(
            f"{_actor(request)} {meta[1]} el expediente {case_number} "
            f"({result.get('estado_anterior')} → {result.get('estado_nuevo')}). "
            f"Motivo: {result.get('motivo')}"
        ),
        antes={"estado": result.get("estado_anterior")},
        despues={"estado": result.get("estado_nuevo"), "motivo": result.get("motivo")},
    )


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteCerrarView(APIView):
    """POST — cerrar expediente (Detective asignado / Comisario)."""

    permission_classes = [CanEditExpedienteJWT]
    parser_classes = [JSONParser, FormParser]

    def post(self, request, case_number: str):
        try:
            result = _svc().change_estado(
                case_number,
                user=request.crimetrack_user,
                accion="cerrar",
                motivo=str(request.data.get("motivo", "")),
            )
            _audit_estado(request, case_number, "cerrar", result)
            return Response(result)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteReabrirView(APIView):
    """POST — reabrir expediente cerrado (solo Comisario/Admin)."""

    permission_classes = [CanManageExpedienteLifecycleJWT]
    parser_classes = [JSONParser, FormParser]

    def post(self, request, case_number: str):
        try:
            result = _svc().change_estado(
                case_number,
                user=request.crimetrack_user,
                accion="reabrir",
                motivo=str(request.data.get("motivo", "")),
            )
            _audit_estado(request, case_number, "reabrir", result)
            return Response(result)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteArchivarView(APIView):
    """POST — archivar expediente cerrado (solo Comisario/Admin)."""

    permission_classes = [CanManageExpedienteLifecycleJWT]
    parser_classes = [JSONParser, FormParser]

    def post(self, request, case_number: str):
        try:
            result = _svc().change_estado(
                case_number,
                user=request.crimetrack_user,
                accion="archivar",
                motivo=str(request.data.get("motivo", "")),
            )
            _audit_estado(request, case_number, "archivar", result)
            return Response(result)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteEliminarView(APIView):
    """DELETE — eliminación lógica del expediente (solo Comisario/Admin)."""

    permission_classes = [CanManageExpedienteLifecycleJWT]
    parser_classes = [JSONParser, FormParser]

    def delete(self, request, case_number: str):
        motivo = str(request.data.get("motivo", "") or request.query_params.get("motivo", ""))
        try:
            result = _svc().change_estado(
                case_number,
                user=request.crimetrack_user,
                accion="eliminar",
                motivo=motivo,
            )
            _audit_estado(request, case_number, "eliminar", result)
            return Response(result)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteCabeceraView(APIView):
    permission_classes = [CanAccessExpedienteJWT]

    @cache_response("exp:cabecera", ttl=300, key_builder=_expediente_case_key)
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
                foto=request.FILES.get("foto"),
            )
            tipo = str(request.data.get("tipo_relacion") or "involucrado")
            nombre = f"{request.data.get('nombres', '')} {request.data.get('apellidos', '')}".strip()
            audit_request(
                request,
                accion="INVOLUCRADO_ADDED",
                tabla="app_caso_involucrado",
                detalle=f"{_actor(request)} agregó al {tipo} {nombre or 's/n'} en el caso {case_number}",
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
            tipo_ev = str(request.data.get("tipo_evidencia", "Multimedia"))
            row = _svc().upload_evidencia(
                case_number,
                user=request.crimetrack_user,
                file_obj=archivo,
                filename=archivo.name,
                tipo_evidencia=tipo_ev,
            )
            hash_corto = str(row.get("hash_sha256") or "")[:16]
            audit_request(
                request,
                accion="EVIDENCE_UPLOADED",
                tabla="app_evidencias",
                detalle=(
                    f"{_actor(request)} cargó evidencia '{archivo.name}' ({tipo_ev}) "
                    f"en el caso {case_number} — SHA-256 {hash_corto}…"
                ),
                despues=row,
            )
            return Response(row, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteBitacoraView(APIView):
    permission_classes = [CanManageBitacoraJWT]
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
            audit_request(
                request,
                accion="CASE_UPDATED",
                tabla="app_expediente_bitacora",
                detalle=(
                    f"{_actor(request)} actualizó el caso {case_number}: "
                    f"estado '{estado}', avance {avance}% — nota de bitácora registrada"
                ),
            )
            return Response(row, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class ExpedienteCierreRequisitosView(APIView):
    """GET — verifica los criterios de cierre (RN-09) del expediente (CU-O25)."""

    permission_classes = [CanAccessExpedienteJWT]

    def get(self, request, case_number: str):
        try:
            return Response(_svc().check_close_requirements(case_number))
        except Exception as exc:
            return _err(exc, 500)


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
        audit_request(
            request,
            accion="CASE_PDF_EXPORTED",
            tabla="app_casos_operativos",
            detalle=f"{_actor(request)} exportó el informe PDF del caso {case_number}",
        )
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_number)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="Informe_Penal_{safe_name}.pdf"'
        )
        return response
