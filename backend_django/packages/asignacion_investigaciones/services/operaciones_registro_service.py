"""
Registro diario operativo: turnos, catálogos de incidentes, ubicaciones e historial de estados.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.auth_service import AuthService
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

FK_ROL_ADMIN = 1
FK_ROL_COMISARIO = 2
FK_ROL_DETECTIVE = 3
FK_ROL_OFICIAL = 4

TURNOS_SEED = [
    ("MANANA", "Mañana", "06:00", "14:00", 1),
    ("TARDE", "Tarde", "14:00", "22:00", 2),
    ("NOCHE", "Noche", "22:00", "06:00", 3),
    ("MADRUGADA", "Madrugada", "00:00", "06:00", 4),
]

TIPOS_SEED = [
    ("ROBO", "Robo", "Sustracción con violencia o intimidación"),
    ("HOMICIDIO", "Homicidio", "Muerte dolosa de una persona"),
    ("AGRESION", "Agresión", "Lesiones o violencia física"),
    ("VANDALISMO", "Vandalismo", "Daños a bienes públicos o privados"),
    ("NARCOTICOS", "Narcóticos", "Posesión o tráfico de sustancias"),
    ("VIOLENCIA_DOMESTICA", "Violencia doméstica", "Violencia intrafamiliar"),
    ("HURTO", "Hurto", "Sustracción sin violencia"),
    ("ACCIDENTE_TRANSITO", "Accidente de tránsito", "Colisión o atropello"),
    ("DISTURBIO", "Disturbio", "Alteración del orden público"),
    ("EMERGENCIA_MEDICA", "Emergencia médica", "Atención médica urgente"),
    ("OTRO", "Otro", "Incidente no clasificado"),
]

ESTADOS_SEED = [
    ("REPORTADO", "Reportado", 1, False),
    ("DESPACHADO", "Despachado", 2, False),
    ("EN_CAMINO", "En camino", 3, False),
    ("EN_LUGAR", "En el lugar", 4, False),
    ("EN_ATENCION", "En atención", 5, False),
    ("RESUELTO", "Atendido", 6, False),
    ("CERRADO", "Cerrado", 7, True),
]

PRIORIDADES_SEED = [
    ("BAJA", "Baja", 1, 1),
    ("MEDIA", "Media", 2, 2),
    ("ALTA", "Alta", 3, 3),
    ("CRITICA", "Crítica", 4, 4),
]

# Alias legado → código catálogo
_ESTADO_ALIASES = {
    "Atendido": "RESUELTO",
    "En el lugar": "EN_LUGAR",
}


def _safe(value: Any) -> Any:
    try:
        if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _json_safe(row: dict[str, Any]) -> dict[str, Any]:
    return {k: _safe(v) for k, v in row.items()}


class OperacionesRegistroService:
    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()
        self.tx.ensure_tables()

    def ensure_seed(self) -> dict[str, int]:
        """Carga catálogos y turnos base si las tablas están vacías."""
        counts = {
            "turnos": self._seed_turnos(),
            "tipos": self._seed_tipos(),
            "estados": self._seed_estados(),
            "prioridades": self._seed_prioridades(),
        }
        return counts

    def _seed_turnos(self) -> int:
        df = self.tx.read_table("app_turnos")
        if not df.empty:
            return len(df)
        for codigo, nombre, ini, fin, orden in TURNOS_SEED:
            self.tx.append_row(
                "app_turnos",
                {
                    "codigo": codigo,
                    "nombre": nombre,
                    "hora_inicio": ini,
                    "hora_fin": fin,
                    "orden": orden,
                    "activo": True,
                },
            )
        return len(TURNOS_SEED)

    def _seed_tipos(self) -> int:
        df = self.tx.read_table("app_tipos_incidente")
        if not df.empty:
            return len(df)
        for i, (codigo, nombre, desc) in enumerate(TIPOS_SEED, start=1):
            self.tx.append_row(
                "app_tipos_incidente",
                {
                    "codigo": codigo,
                    "nombre": nombre,
                    "descripcion": desc,
                    "orden": i,
                    "activo": True,
                },
            )
        return len(TIPOS_SEED)

    def _seed_estados(self) -> int:
        df = self.tx.read_table("app_estados_incidente")
        if not df.empty:
            return len(df)
        for codigo, nombre, orden, es_final in ESTADOS_SEED:
            self.tx.append_row(
                "app_estados_incidente",
                {
                    "codigo": codigo,
                    "nombre": nombre,
                    "orden": orden,
                    "es_final": es_final,
                    "activo": True,
                },
            )
        return len(ESTADOS_SEED)

    def _seed_prioridades(self) -> int:
        df = self.tx.read_table("app_prioridades_incidente")
        if not df.empty:
            return len(df)
        for codigo, nombre, nivel, orden in PRIORIDADES_SEED:
            self.tx.append_row(
                "app_prioridades_incidente",
                {
                    "codigo": codigo,
                    "nombre": nombre,
                    "nivel": nivel,
                    "orden": orden,
                    "activo": True,
                },
            )
        return len(PRIORIDADES_SEED)

    # ── Catálogos ─────────────────────────────────────────────────────
    def list_tipos(self, *, activo_only: bool = True) -> list[dict[str, Any]]:
        self.ensure_seed()
        df = self.tx.read_table("app_tipos_incidente")
        if activo_only and not df.empty:
            df = df[df["activo"].astype(bool)]
        return [
            _json_safe(r)
            for r in df.sort_values("orden").to_dict(orient="records")
        ]

    def list_estados(self, *, activo_only: bool = True) -> list[dict[str, Any]]:
        self.ensure_seed()
        df = self.tx.read_table("app_estados_incidente")
        if activo_only and not df.empty:
            df = df[df["activo"].astype(bool)]
        return [
            _json_safe(r)
            for r in df.sort_values("orden").to_dict(orient="records")
        ]

    def list_prioridades(self, *, activo_only: bool = True) -> list[dict[str, Any]]:
        self.ensure_seed()
        df = self.tx.read_table("app_prioridades_incidente")
        if activo_only and not df.empty:
            df = df[df["activo"].astype(bool)]
        return [
            _json_safe(r)
            for r in df.sort_values("orden").to_dict(orient="records")
        ]

    def catalogos_ui(self) -> dict[str, Any]:
        tipos = self.list_tipos()
        estados = self.list_estados()
        prioridades = self.list_prioridades()
        return {
            "tipos_incidente": [t["nombre"] for t in tipos],
            "estados_incidente": [e["nombre"] for e in estados],
            "prioridades": [p["nombre"] for p in prioridades],
            "tipos": tipos,
            "estados": estados,
            "prioridades_detalle": prioridades,
            "turnos": self.list_turnos(),
            "distritos": self.list_distritos(),
        }

    def resolve_tipo(self, value: str) -> dict[str, Any]:
        self.ensure_seed()
        df = self.tx.read_table("app_tipos_incidente")
        val = str(value or "").strip()
        if not val:
            val = "Otro"
        for col in ("nombre", "codigo"):
            hit = df[df[col].astype(str).str.lower() == val.lower()]
            if not hit.empty:
                return hit.iloc[0].to_dict()
        hit = df[df["codigo"].astype(str).str.upper() == "OTRO"]
        return hit.iloc[0].to_dict() if not hit.empty else df.iloc[0].to_dict()

    def resolve_estado(self, value: str) -> dict[str, Any]:
        self.ensure_seed()
        df = self.tx.read_table("app_estados_incidente")
        val = str(value or "").strip()
        codigo = _ESTADO_ALIASES.get(val, val).upper().replace(" ", "_")
        for col in ("codigo", "nombre"):
            hit = df[df[col].astype(str).str.lower() == val.lower()]
            if not hit.empty:
                return hit.iloc[0].to_dict()
        hit = df[df["codigo"].astype(str).str.upper() == codigo]
        if not hit.empty:
            return hit.iloc[0].to_dict()
        hit = df[df["codigo"].astype(str).str.upper() == "REPORTADO"]
        return hit.iloc[0].to_dict()

    def resolve_prioridad(self, value: str) -> dict[str, Any]:
        self.ensure_seed()
        df = self.tx.read_table("app_prioridades_incidente")
        val = str(value or "").strip() or "Media"
        for col in ("nombre", "codigo"):
            hit = df[df[col].astype(str).str.lower() == val.lower()]
            if not hit.empty:
                return hit.iloc[0].to_dict()
        hit = df[df["codigo"].astype(str).str.upper() == "MEDIA"]
        return hit.iloc[0].to_dict()

    # ── Ubicaciones ───────────────────────────────────────────────────
    def create_ubicacion(
        self,
        *,
        direccion: str,
        barrio: str = "",
        fk_distrito: int | None = None,
        latitud: str = "",
        longitud: str = "",
        referencia: str = "",
    ) -> dict[str, Any]:
        if not str(direccion).strip():
            raise ValueError("La dirección es obligatoria.")
        distrito_nombre = ""
        if fk_distrito:
            dist_df = self.tx.read_table("app_distritos_policiales")
            hit = dist_df[dist_df["id_distrito"].astype(int) == int(fk_distrito)]
            if not hit.empty:
                distrito_nombre = str(hit.iloc[0].get("nombre") or "")
        row = {
            "direccion": str(direccion).strip(),
            "barrio": str(barrio or "").strip(),
            "fk_distrito": int(fk_distrito) if fk_distrito else None,
            "distrito_nombre": distrito_nombre,
            "latitud": str(latitud or "").strip(),
            "longitud": str(longitud or "").strip(),
            "referencia": str(referencia or "").strip(),
            "creado_en": utc_now_iso(),
        }
        created = self.tx.append_row("app_ubicaciones_incidente", row)
        return _json_safe(created)

    def ubicacion_resumen(self, ubic: dict[str, Any]) -> str:
        parts = [str(ubic.get("direccion") or "").strip()]
        barrio = str(ubic.get("barrio") or "").strip()
        if barrio:
            parts.append(barrio)
        distrito = str(ubic.get("distrito_nombre") or "").strip()
        if distrito:
            parts.append(distrito)
        return " · ".join(p for p in parts if p)

    def get_ubicacion(self, fk_ubicacion: int) -> dict[str, Any] | None:
        df = self.tx.read_table("app_ubicaciones_incidente")
        hit = df[df["id_ubicacion"].astype(int) == int(fk_ubicacion)]
        return _json_safe(hit.iloc[0].to_dict()) if not hit.empty else None

    def list_distritos(self) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_distritos_policiales")
        if df.empty:
            return []
        sub = df[df.get("activo", True).astype(bool)] if "activo" in df.columns else df
        return [_json_safe(r) for r in sub.sort_values("id_distrito").to_dict(orient="records")]

    # ── Turnos ────────────────────────────────────────────────────────
    def list_turnos(self, *, activo_only: bool = True) -> list[dict[str, Any]]:
        self.ensure_seed()
        df = self.tx.read_table("app_turnos")
        if activo_only and not df.empty:
            df = df[df["activo"].astype(bool)]
        return [
            _json_safe(r)
            for r in df.sort_values("orden").to_dict(orient="records")
        ]

    def get_turno(self, fk_turno: int) -> dict[str, Any] | None:
        df = self.tx.read_table("app_turnos")
        hit = df[df["id_turno"].astype(int) == int(fk_turno)]
        return _json_safe(hit.iloc[0].to_dict()) if not hit.empty else None

    def turno_activo_para_fecha(self, when_iso: str | None = None) -> dict[str, Any] | None:
        """Turno operativo vigente según asignaciones del día."""
        fecha = str(when_iso or utc_now_iso())[:10]
        df = self.tx.read_table("app_asignacion_turnos")
        if df.empty:
            return None
        sub = df[
            (df["fecha"].astype(str).str[:10] == fecha)
            & (df["estado"].astype(str) == "Activa")
        ]
        if sub.empty:
            return None
        row = sub.sort_values("id_asignacion_turno", ascending=False).iloc[0].to_dict()
        turno = self.get_turno(int(row["fk_turno"]))
        return turno

    def list_asignaciones_turno(
        self, *, fecha: str = "", fk_turno: int | None = None
    ) -> list[dict[str, Any]]:
        self.ensure_seed()
        df = self.tx.read_table("app_asignacion_turnos")
        if df.empty:
            return []
        if fecha:
            df = df[df["fecha"].astype(str).str[:10] == str(fecha)[:10]]
        if fk_turno is not None:
            df = df[df["fk_turno"].astype(int) == int(fk_turno)]
        return [
            _json_safe(r)
            for r in df.sort_values("id_asignacion_turno", ascending=False).to_dict(orient="records")
        ]

    def personal_para_turnos(self) -> list[dict[str, Any]]:
        users = AuthService._normalize_users_df(self.tx.read_table("app_usuarios"))
        if users.empty:
            return []
        roles = {1: "Admin", 2: "Comisario", 3: "Detective", 4: "Oficial"}
        allowed = {FK_ROL_ADMIN, FK_ROL_COMISARIO, FK_ROL_DETECTIVE, FK_ROL_OFICIAL}
        items = []
        for row in users.to_dict(orient="records"):
            rol = int(row.get("fk_rol") or 0)
            if rol not in allowed:
                continue
            if str(row.get("estado_cuenta", "")).lower() != "activa":
                continue
            items.append(
                {
                    "id_usuario": int(row["id_usuario"]),
                    "nombres": row.get("nombres"),
                    "apellidos": row.get("apellidos"),
                    "numero_placa": row.get("numero_placa"),
                    "fk_rol": rol,
                    "nombre_rol": roles.get(rol, ""),
                    "etiqueta": (
                        f"{row.get('nombres', '')} {row.get('apellidos', '')} "
                        f"({row.get('numero_placa', '')})"
                    ).strip(),
                }
            )
        items.sort(key=lambda x: (x["fk_rol"], str(x["apellidos"])))
        return items

    def asignar_turno(
        self,
        *,
        fk_turno: int,
        fk_usuario: int,
        fecha: str,
        actor: dict[str, Any],
        hora_inicio: str = "",
        hora_fin: str = "",
        notas: str = "",
    ) -> dict[str, Any]:
        turno = self.get_turno(int(fk_turno))
        if not turno:
            raise ValueError("Turno no encontrado.")
        users = AuthService._normalize_users_df(self.tx.read_table("app_usuarios"))
        urow = users[users["id_usuario"].astype(int) == int(fk_usuario)]
        if urow.empty:
            raise ValueError("Usuario no encontrado.")
        user = urow.iloc[0].to_dict()
        rol = int(user.get("fk_rol") or 0)
        if rol not in {FK_ROL_ADMIN, FK_ROL_COMISARIO, FK_ROL_DETECTIVE, FK_ROL_OFICIAL}:
            raise ValueError("Solo oficiales, detectives, comisarios o administradores pueden asignarse a turnos.")
        fecha_str = str(fecha or date.today().isoformat())[:10]
        df = self.tx.read_table("app_asignacion_turnos")
        dup = df[
            (df["fk_turno"].astype(int) == int(fk_turno))
            & (df["fk_usuario"].astype(int) == int(fk_usuario))
            & (df["fecha"].astype(str).str[:10] == fecha_str)
            & (df["estado"].astype(str) == "Activa")
        ]
        if not dup.empty:
            raise ValueError("El usuario ya tiene una asignación activa en ese turno y fecha.")
        roles = {1: "Admin", 2: "Comisario", 3: "Detective", 4: "Oficial"}
        row = {
            "fk_turno": int(fk_turno),
            "turno_nombre": str(turno.get("nombre") or ""),
            "fk_usuario": int(fk_usuario),
            "usuario_nombre": f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip(),
            "usuario_placa": str(user.get("numero_placa") or ""),
            "fk_rol": rol,
            "rol_nombre": roles.get(rol, ""),
            "fecha": fecha_str,
            "hora_inicio_efectiva": str(hora_inicio or turno.get("hora_inicio") or ""),
            "hora_fin_efectiva": str(hora_fin or turno.get("hora_fin") or ""),
            "estado": "Activa",
            "notas": str(notas or "").strip(),
            "creado_en": utc_now_iso(),
        }
        created = self.tx.append_row("app_asignacion_turnos", row)
        return _json_safe(created)

    def cerrar_asignacion_turno(self, fk_asignacion: int) -> dict[str, Any]:
        df = self.tx.read_table("app_asignacion_turnos")
        mask = df["id_asignacion_turno"].astype(int) == int(fk_asignacion)
        if not mask.any():
            raise ValueError("Asignación no encontrada.")
        df.loc[mask, "estado"] = "Cerrada"
        self.tx.write_table("app_asignacion_turnos", df)
        return _json_safe(df[mask].iloc[0].to_dict())

    def personal_en_turno(self, fecha: str | None = None) -> list[dict[str, Any]]:
        fecha_str = str(fecha or date.today().isoformat())[:10]
        return self.list_asignaciones_turno(fecha=fecha_str)

    # ── Historial de estados ──────────────────────────────────────────
    def registrar_cambio_estado(
        self,
        *,
        fk_incidente: int,
        estado_anterior: str,
        estado_nuevo: str,
        actor: dict[str, Any] | None = None,
        comentario: str = "",
    ) -> dict[str, Any]:
        est_ant = self.resolve_estado(estado_anterior) if estado_anterior else None
        est_new = self.resolve_estado(estado_nuevo)
        row = {
            "fk_incidente": int(fk_incidente),
            "fk_estado_anterior": int(est_ant["id_estado"]) if est_ant else None,
            "fk_estado_nuevo": int(est_new["id_estado"]),
            "estado_anterior": str(estado_anterior or ""),
            "estado_nuevo": str(est_new.get("nombre") or estado_nuevo),
            "fk_usuario": int(actor["id_usuario"]) if actor else None,
            "usuario_nombre": (
                f"{actor.get('nombres', '')} {actor.get('apellidos', '')}".strip()
                if actor
                else "Sistema"
            ),
            "comentario": str(comentario or "").strip(),
            "fecha_hora": utc_now_iso(),
        }
        created = self.tx.append_row("app_incidente_estado_historial", row)
        return _json_safe(created)

    def historial_incidente(self, fk_incidente: int) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_incidente_estado_historial")
        if df.empty:
            return []
        sub = df[df["fk_incidente"].astype(int) == int(fk_incidente)]
        return [
            _json_safe(r)
            for r in sub.sort_values("id_historial").to_dict(orient="records")
        ]

    def enrich_incidente(self, row: dict[str, Any]) -> dict[str, Any]:
        item = _json_safe(row)
        fk_u = item.get("fk_ubicacion")
        if fk_u:
            ubic = self.get_ubicacion(int(fk_u))
            if ubic:
                item["ubicacion_detalle"] = ubic
        item["historial"] = self.historial_incidente(int(item["id_incidente"]))
        return item
