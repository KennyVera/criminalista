from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.asignacion_investigaciones.permissions import (
    IsComisarioJWT,
    IsDespachoJWT,
    IsOficialJWT,
)
from packages.asignacion_investigaciones.services.operaciones_registro_service import (
    OperacionesRegistroService,
)
from packages.asignacion_investigaciones.services.patrullas_service import (
    ESTADOS_PATRULLA,
    PatrullaService,
)
from packages.shared.audit import audit_request


def _actor(request) -> str:
    u = getattr(request, "crimetrack_user", {}) or {}
    nombre = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()
    return nombre or str(u.get("email") or "Usuario")


def _err(exc: Exception, code=400):
    return Response({"error": str(exc)}, status=code)


def _svc() -> PatrullaService:
    return PatrullaService()


# ── CU-O77: Comisario ─────────────────────────────────────────────────
def _registro() -> OperacionesRegistroService:
    return OperacionesRegistroService()


@method_decorator(csrf_exempt, name="dispatch")
class PatrullaCatalogosView(APIView):
    """GET — catálogos operativos (tipos, estados, prioridades, turnos, distritos)."""

    permission_classes = [IsDespachoJWT]

    def get(self, request):
        data = _registro().catalogos_ui()
        data["estados_patrulla"] = list(ESTADOS_PATRULLA)
        return Response(data)


@method_decorator(csrf_exempt, name="dispatch")
class OficialesDisponiblesView(APIView):
    """GET — oficiales y su disponibilidad para conformar patrullas (CU-O77)."""

    permission_classes = [IsComisarioJWT]

    def get(self, request):
        return Response({"items": _svc().list_oficiales()})


@method_decorator(csrf_exempt, name="dispatch")
class PatrullasView(APIView):
    """GET lista patrullas (despacho) / POST crea patrulla (solo Comisario, CU-O77)."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsComisarioJWT()]
        return [IsDespachoJWT()]

    def get(self, request):
        estado = request.query_params.get("estado", "")
        return Response({"items": _svc().list_patrullas(estado=estado)})

    def post(self, request):
        data = request.data or {}
        try:
            row = _svc().create_patrulla(
                comisario=request.crimetrack_user,
                sector=str(data.get("sector", "")),
                turno=str(data.get("turno", "")),
                fk_turno=int(data["fk_turno"]) if data.get("fk_turno") else None,
                notas=str(data.get("notas", "")),
            )
        except ValueError as exc:
            return _err(exc)
        audit_request(
            request,
            accion="PATROL_CREATED",
            tabla="app_patrullas",
            detalle=f"{_actor(request)} creó la patrulla {row.get('codigo')} (sector {row.get('sector')}, turno {row.get('turno')})",
            despues=row,
        )
        return Response(row, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class PatrullaAsignarOficialesView(APIView):
    """POST — CU-O77: asigna oficiales a la patrulla."""

    permission_classes = [IsComisarioJWT]

    def post(self, request, fk_patrulla: int):
        data = request.data or {}
        ids = data.get("oficial_ids") or []
        if isinstance(ids, (int, str)):
            ids = [ids]
        try:
            ids = [int(x) for x in ids]
            result = _svc().assign_oficiales(
                int(fk_patrulla), oficial_ids=ids, comisario=request.crimetrack_user
            )
        except ValueError as exc:
            return _err(exc)
        audit_request(
            request,
            accion="PATROL_ASSIGNED",
            tabla="app_patrulla_oficiales",
            detalle=(
                f"{_actor(request)} asignó {result['total_asignados']} oficial(es) "
                f"a la patrulla {result.get('codigo')}"
            ),
            despues=result,
        )
        return Response(result, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class PatrullaOficialDetailView(APIView):
    """DELETE — remueve un oficial de la patrulla (CU-O77)."""

    permission_classes = [IsComisarioJWT]

    def delete(self, request, fk_patrulla: int, fk_oficial: int):
        try:
            result = _svc().remove_oficial(int(fk_patrulla), int(fk_oficial))
        except ValueError as exc:
            return _err(exc)
        audit_request(
            request,
            accion="PATROL_OFFICER_REMOVED",
            tabla="app_patrulla_oficiales",
            detalle=f"{_actor(request)} removió al oficial #{fk_oficial} de la patrulla #{fk_patrulla}",
        )
        return Response(result)


# ── Incidentes: registro (Oficial/Operador) y tablero (Comisario) ─────
@method_decorator(csrf_exempt, name="dispatch")
class IncidentesView(APIView):
    """GET tablero de incidentes (Comisario) / POST registra incidente (Oficial u operador)."""

    def get_permissions(self):
        # Registrar lo puede hacer el Oficial u operador; el tablero general es del Comisario.
        if self.request.method == "POST":
            return [IsDespachoJWT()]
        return [IsComisarioJWT()]

    def get(self, request):
        estado = request.query_params.get("estado", "")
        return Response({"items": _svc().list_incidentes(estado=estado)})

    def post(self, request):
        data = request.data or {}
        try:
            row = _svc().create_incidente(
                operador=request.crimetrack_user,
                tipo=str(data.get("tipo", "")),
                descripcion=str(data.get("descripcion", "")),
                ubicacion=str(data.get("ubicacion", "")),
                direccion=str(data.get("direccion", "")),
                barrio=str(data.get("barrio", "")),
                fk_distrito=int(data["fk_distrito"]) if data.get("fk_distrito") else None,
                latitud=str(data.get("latitud", "")),
                longitud=str(data.get("longitud", "")),
                prioridad=str(data.get("prioridad", "Media")),
                reportante=str(data.get("reportante", "")),
                fk_tipo_incidente=int(data["fk_tipo_incidente"]) if data.get("fk_tipo_incidente") else None,
                fk_prioridad_incidente=int(data["fk_prioridad_incidente"])
                if data.get("fk_prioridad_incidente")
                else None,
            )
        except ValueError as exc:
            return _err(exc)
        audit_request(
            request,
            accion="INCIDENT_REPORTED",
            tabla="app_incidentes",
            detalle=f"{_actor(request)} registró el incidente {row.get('codigo')} ({row.get('tipo')}) en {row.get('ubicacion')}",
            despues=row,
        )
        return Response(row, status=status.HTTP_201_CREATED)


# ── CU-O78: el COMISARIO evalúa, despacha, aprueba o devuelve ─────────
@method_decorator(csrf_exempt, name="dispatch")
class DespacharView(APIView):
    """POST — CU-O78: solo el Comisario asigna patrulla, define prioridad y despacha."""

    permission_classes = [IsComisarioJWT]

    def post(self, request, fk_incidente: int):
        data = request.data or {}
        try:
            fk_patrulla = int(data.get("fk_patrulla"))
        except (TypeError, ValueError):
            return _err(ValueError("Debe indicar la patrulla a despachar."))
        try:
            result = _svc().dispatch(
                int(fk_incidente),
                fk_patrulla=fk_patrulla,
                comisario=request.crimetrack_user,
                prioridad=str(data.get("prioridad", "")),
                notas=str(data.get("notas", "")),
            )
        except ValueError as exc:
            return _err(exc)
        inc = result["incidente"]
        audit_request(
            request,
            accion="PATROL_DISPATCHED",
            tabla="app_incidentes",
            detalle=(
                f"{_actor(request)} despachó la patrulla {inc.get('patrulla_codigo')} "
                f"al incidente {inc.get('codigo')} ({inc.get('tipo')})"
            ),
            antes=result["antes"],
            despues=result["despues"],
        )
        return Response(inc, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class IncidenteCerrarView(APIView):
    """POST — el Comisario revisa el parte y aprueba el cierre (Atendido→Cerrado)."""

    permission_classes = [IsComisarioJWT]

    def post(self, request, fk_incidente: int):
        try:
            result = _svc().aprobar_cierre(int(fk_incidente), comisario=request.crimetrack_user)
        except ValueError as exc:
            return _err(exc)
        inc = result["incidente"]
        audit_request(
            request,
            accion="INCIDENT_CLOSED",
            tabla="app_incidentes",
            detalle=f"{_actor(request)} aprobó el cierre del incidente {inc.get('codigo')}",
            antes=result["antes"],
            despues=result["despues"],
        )
        return Response(inc, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class IncidenteDevolverView(APIView):
    """POST — el Comisario devuelve el caso para corrección (Atendido→En atención)."""

    permission_classes = [IsComisarioJWT]

    def post(self, request, fk_incidente: int):
        data = request.data or {}
        try:
            result = _svc().devolver_incidente(
                int(fk_incidente),
                comisario=request.crimetrack_user,
                motivo=str(data.get("motivo", "")),
            )
        except ValueError as exc:
            return _err(exc)
        inc = result["incidente"]
        audit_request(
            request,
            accion="INCIDENT_RETURNED",
            tabla="app_incidentes",
            detalle=f"{_actor(request)} devolvió el incidente {inc.get('codigo')} para corrección",
            antes=result["antes"],
            despues=result["despues"],
        )
        return Response(inc, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class IncidenteDetailView(APIView):
    """GET — detalle de incidente con ubicación e historial de estados."""

    permission_classes = [IsDespachoJWT]

    def get(self, request, fk_incidente: int):
        row = _svc().get_incidente(int(fk_incidente))
        if not row:
            return _err(ValueError("Incidente no encontrado."), 404)
        return Response(row)


@method_decorator(csrf_exempt, name="dispatch")
class TurnosView(APIView):
    """GET turnos / GET asignaciones del día / POST asignar personal a turno."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsComisarioJWT()]
        return [IsDespachoJWT()]

    def get(self, request):
        fecha = str(request.query_params.get("fecha", "")).strip()
        fk_turno = request.query_params.get("fk_turno")
        fk_int = int(fk_turno) if fk_turno else None
        reg = _registro()
        return Response(
            {
                "turnos": reg.list_turnos(),
                "asignaciones": reg.list_asignaciones_turno(fecha=fecha, fk_turno=fk_int),
                "personal": reg.personal_para_turnos(),
                "distritos": reg.list_distritos(),
            }
        )

    def post(self, request):
        data = request.data or {}
        try:
            row = _registro().asignar_turno(
                fk_turno=int(data["fk_turno"]),
                fk_usuario=int(data["fk_usuario"]),
                fecha=str(data.get("fecha", "")),
                actor=request.crimetrack_user,
                hora_inicio=str(data.get("hora_inicio", "")),
                hora_fin=str(data.get("hora_fin", "")),
                notas=str(data.get("notas", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            return _err(exc if isinstance(exc, ValueError) else ValueError("Datos incompletos."))
        audit_request(
            request,
            accion="TURNO_ASSIGNED",
            tabla="app_asignacion_turnos",
            detalle=f"{_actor(request)} asignó turno {row.get('turno_nombre')} a {row.get('usuario_nombre')}",
            despues=row,
        )
        return Response(row, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class AsignacionTurnoDetailView(APIView):
    """POST — cerrar asignación de turno."""

    permission_classes = [IsComisarioJWT]

    def post(self, request, fk_asignacion: int):
        try:
            row = _registro().cerrar_asignacion_turno(int(fk_asignacion))
        except ValueError as exc:
            return _err(exc)
        audit_request(
            request,
            accion="TURNO_ASSIGNMENT_CLOSED",
            tabla="app_asignacion_turnos",
            detalle=f"{_actor(request)} cerró asignación de turno #{fk_asignacion}",
            despues=row,
        )
        return Response(row)


# ── Oficial receptor: recibe, atiende y reporta ───────────────────────
@method_decorator(csrf_exempt, name="dispatch")
class MisPatrullasView(APIView):
    """GET — patrullas e incidentes asignados al oficial autenticado (recepción y atención)."""

    permission_classes = [IsOficialJWT]

    def get(self, request):
        fk = int(request.crimetrack_user["id_usuario"])
        return Response(
            {
                "patrullas": _svc().mis_patrullas(fk),
                "incidentes": _svc().mis_incidentes(fk),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class IncidenteAvanzarView(APIView):
    """POST — el oficial acepta/avanza: Despachado→En camino→En el lugar→En atención."""

    permission_classes = [IsOficialJWT]

    def post(self, request, fk_incidente: int):
        data = request.data or {}
        try:
            result = _svc().avanzar_incidente(
                int(fk_incidente),
                oficial=request.crimetrack_user,
                nota=str(data.get("nota", "")),
            )
        except ValueError as exc:
            return _err(exc)
        inc = result["incidente"]
        audit_request(
            request,
            accion="INCIDENT_STATUS_UPDATED",
            tabla="app_incidentes",
            detalle=(
                f"{_actor(request)} actualizó el incidente {inc.get('codigo')}: "
                f"{result['antes']['incidente_estado']} → {result['despues']['incidente_estado']}"
            ),
            antes=result["antes"],
            despues=result["despues"],
        )
        return Response(inc, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class IncidenteFinalizarView(APIView):
    """POST — el oficial finaliza la atención y genera el parte (En atención→Atendido)."""

    permission_classes = [IsOficialJWT]

    def post(self, request, fk_incidente: int):
        data = request.data or {}
        try:
            result = _svc().finalizar_atencion(
                int(fk_incidente),
                oficial=request.crimetrack_user,
                resultado=str(data.get("resultado", "")),
                parte=str(data.get("parte", "")),
            )
        except ValueError as exc:
            return _err(exc)
        inc = result["incidente"]
        audit_request(
            request,
            accion="INCIDENT_RESOLVED",
            tabla="app_incidentes",
            detalle=f"{_actor(request)} finalizó la atención del incidente {inc.get('codigo')} y generó el parte",
            antes=result["antes"],
            despues=result["despues"],
        )
        return Response(inc, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class IncidenteApoyoView(APIView):
    """POST — el oficial solicita apoyo operativo."""

    permission_classes = [IsOficialJWT]

    def post(self, request, fk_incidente: int):
        data = request.data or {}
        try:
            result = _svc().solicitar_apoyo(
                int(fk_incidente),
                oficial=request.crimetrack_user,
                nota=str(data.get("nota", "")),
            )
        except ValueError as exc:
            return _err(exc)
        inc = result["incidente"]
        audit_request(
            request,
            accion="SUPPORT_REQUESTED",
            tabla="app_incidentes",
            detalle=f"{_actor(request)} solicitó apoyo para el incidente {inc.get('codigo')}",
            despues={"apoyo_solicitado": True},
        )
        return Response(inc, status=status.HTTP_200_OK)
