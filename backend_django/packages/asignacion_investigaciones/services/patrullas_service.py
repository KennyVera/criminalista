"""
Servicio de Operaciones de Patrulla (CU-O77, CU-O78) — extensión operativa de P05.

CU-O77 — Asignar patrulla a oficiales (actor: Comisario).
CU-O78 — Despachar patrulla a incidente (actor: Oficial / Operador de Central; recibe Oficial de patrulla).

Persistencia en MinIO/Parquet (TransactionalMinioStore): app_patrullas,
app_patrulla_oficiales, app_incidentes.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.auth_service import AuthService
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

FK_ROL_OFICIAL = 4
FK_ROL_COMISARIO = 2

# Estados de patrulla y transiciones válidas.
ESTADOS_PATRULLA = ("Disponible", "Despachada", "En ruta", "En sitio", "Fuera de servicio")
# Estados de incidente (flujo: registro → despacho → recepción → atención → cierre).
ESTADOS_INCIDENTE = (
    "Reportado",   # registrado por oficial u operador
    "Despachado",  # comisario asignó patrulla y despachó
    "En camino",   # oficial aceptó la asignación
    "En el lugar", # oficial llegó al sitio
    "En atención", # oficial atendiendo el incidente
    "Atendido",    # oficial finalizó y generó el parte
    "Cerrado",     # comisario aprobó el cierre
)
PRIORIDADES = ("Alta", "Media", "Baja")
TIPOS_INCIDENTE = (
    "Robo",
    "Hurto",
    "Violencia intrafamiliar",
    "Accidente de tránsito",
    "Disturbio",
    "Persona sospechosa",
    "Emergencia médica",
    "Otro",
)
ESTADO_OFICIAL_ACTIVO = "Activo"
ESTADO_OFICIAL_REMOVIDO = "Removido"


def _safe(value: Any) -> Any:
    try:
        if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _json_safe(row: dict[str, Any]) -> dict[str, Any]:
    return {k: _safe(v) for k, v in row.items()}


class PatrullaService:
    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()
        self.tx.ensure_tables()

    # ── Helpers ────────────────────────────────────────────────────────
    def _users_df(self) -> pd.DataFrame:
        return AuthService._normalize_users_df(self.tx.read_table("app_usuarios"))

    @staticmethod
    def _persona(user: dict[str, Any]) -> str:
        return f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip()

    def _next_codigo(self, df: pd.DataFrame) -> str:
        n = (len(df) + 1) if df is not None else 1
        return f"PAT-{n:03d}"

    def _next_incidente_codigo(self, df: pd.DataFrame) -> str:
        n = (len(df) + 1) if df is not None else 1
        return f"INC-{n:04d}"

    # ── Oficiales disponibles ──────────────────────────────────────────
    def list_oficiales(self) -> list[dict[str, Any]]:
        users = self._users_df()
        if users.empty:
            return []
        oficiales = users[users["fk_rol"].astype("Int64") == FK_ROL_OFICIAL]
        # Oficiales ya asignados a una patrulla activa.
        po = self.tx.read_table("app_patrulla_oficiales")
        asignados: set[int] = set()
        if not po.empty:
            activos = po[po["estado"].astype(str) == ESTADO_OFICIAL_ACTIVO]
            asignados = {int(x) for x in activos["fk_oficial"].astype(int)}
        items = []
        for row in oficiales.to_dict(orient="records"):
            uid = int(row["id_usuario"])
            items.append(
                {
                    "id_usuario": uid,
                    "nombres": row.get("nombres"),
                    "apellidos": row.get("apellidos"),
                    "numero_placa": row.get("numero_placa"),
                    "estado_cuenta": row.get("estado_cuenta"),
                    "asignado": uid in asignados,
                    "disponible": uid not in asignados
                    and str(row.get("estado_cuenta", "")).lower() == "activa",
                    "etiqueta": f"Of. {row.get('apellidos', '')}, {row.get('nombres', '')} ({row.get('numero_placa', '')})".strip(),
                }
            )
        items.sort(key=lambda x: (not x["disponible"], str(x["apellidos"])))
        return items

    # ── Patrullas ──────────────────────────────────────────────────────
    def list_patrullas(self, *, estado: str = "") -> list[dict[str, Any]]:
        df = self.tx.read_table("app_patrullas")
        if df.empty:
            return []
        if estado:
            df = df[df["estado"].astype(str) == estado]
        po = self.tx.read_table("app_patrulla_oficiales")
        out = []
        for row in df.sort_values("id_patrulla", ascending=False).to_dict(orient="records"):
            pid = int(row["id_patrulla"])
            oficiales = self._oficiales_de_patrulla(po, pid)
            item = _json_safe(row)
            item["oficiales"] = oficiales
            item["total_oficiales"] = len(oficiales)
            out.append(item)
        return out

    @staticmethod
    def _oficiales_de_patrulla(po: pd.DataFrame, fk_patrulla: int) -> list[dict[str, Any]]:
        if po is None or po.empty:
            return []
        sub = po[
            (po["fk_patrulla"].astype(int) == fk_patrulla)
            & (po["estado"].astype(str) == ESTADO_OFICIAL_ACTIVO)
        ]
        return [_json_safe(r) for r in sub.to_dict(orient="records")]

    def create_patrulla(
        self,
        *,
        comisario: dict[str, Any],
        sector: str,
        turno: str,
        notas: str = "",
    ) -> dict[str, Any]:
        if not str(sector).strip():
            raise ValueError("El sector es obligatorio.")
        if not str(turno).strip():
            raise ValueError("El turno es obligatorio.")
        df = self.tx.read_table("app_patrullas")
        now = utc_now_iso()
        row = {
            "codigo": self._next_codigo(df),
            "sector": str(sector).strip(),
            "turno": str(turno).strip(),
            "estado": "Disponible",
            "fk_comisario": int(comisario["id_usuario"]),
            "comisario_nombre": self._persona(comisario),
            "notas": str(notas or "").strip(),
            "fecha_creacion": now,
            "fecha_actualizacion": now,
            "activo": True,
        }
        created = self.tx.append_row("app_patrullas", row)
        return _json_safe(created)

    def assign_oficiales(
        self,
        fk_patrulla: int,
        *,
        oficial_ids: list[int],
        comisario: dict[str, Any],
    ) -> dict[str, Any]:
        """CU-O77: asigna uno o más oficiales a la patrulla (sin doble asignación activa)."""
        patrullas = self.tx.read_table("app_patrullas")
        prow = patrullas[patrullas["id_patrulla"].astype(int) == int(fk_patrulla)]
        if prow.empty:
            raise ValueError("Patrulla no encontrada.")

        if not oficial_ids:
            raise ValueError("Debe seleccionar al menos un oficial.")

        users = self._users_df()
        po = self.tx.read_table("app_patrulla_oficiales")
        activos = (
            po[po["estado"].astype(str) == ESTADO_OFICIAL_ACTIVO]
            if not po.empty
            else po
        )

        agregados = []
        now = utc_now_iso()
        for oid in oficial_ids:
            oid = int(oid)
            urow = users[users["id_usuario"].astype(int) == oid]
            if urow.empty or int(urow.iloc[0]["fk_rol"]) != FK_ROL_OFICIAL:
                raise ValueError(f"El usuario {oid} no es un oficial válido.")
            of = urow.iloc[0].to_dict()
            # RN: sin doble asignación activa en otra patrulla.
            if not activos.empty:
                dup = activos[
                    (activos["fk_oficial"].astype(int) == oid)
                    & (activos["fk_patrulla"].astype(int) != int(fk_patrulla))
                ]
                if not dup.empty:
                    raise ValueError(
                        f"El oficial {self._persona(of)} ya está activo en otra patrulla."
                    )
            # Evitar duplicado en la misma patrulla.
            if not activos.empty:
                ya = activos[
                    (activos["fk_oficial"].astype(int) == oid)
                    & (activos["fk_patrulla"].astype(int) == int(fk_patrulla))
                ]
                if not ya.empty:
                    continue
            rol_patrulla = "Líder" if not agregados and self._oficiales_de_patrulla(po, int(fk_patrulla)) == [] else "Acompañante"
            created = self.tx.append_row(
                "app_patrulla_oficiales",
                {
                    "fk_patrulla": int(fk_patrulla),
                    "fk_oficial": oid,
                    "oficial_nombre": self._persona(of),
                    "oficial_placa": of.get("numero_placa"),
                    "rol_patrulla": rol_patrulla,
                    "fecha_asignacion": now,
                    "estado": ESTADO_OFICIAL_ACTIVO,
                },
            )
            agregados.append(_json_safe(created))
            # Recargar activos para validar duplicados subsecuentes.
            po = self.tx.read_table("app_patrulla_oficiales")
            activos = po[po["estado"].astype(str) == ESTADO_OFICIAL_ACTIVO]

        self._touch_patrulla(int(fk_patrulla))
        return {
            "fk_patrulla": int(fk_patrulla),
            "codigo": str(prow.iloc[0]["codigo"]),
            "asignados": agregados,
            "total_asignados": len(agregados),
        }

    def remove_oficial(self, fk_patrulla: int, fk_oficial: int) -> dict[str, Any]:
        po = self.tx.read_table("app_patrulla_oficiales")
        if po.empty:
            raise ValueError("No hay oficiales asignados.")
        mask = (
            (po["fk_patrulla"].astype(int) == int(fk_patrulla))
            & (po["fk_oficial"].astype(int) == int(fk_oficial))
            & (po["estado"].astype(str) == ESTADO_OFICIAL_ACTIVO)
        )
        if not mask.any():
            raise ValueError("El oficial no está asignado a esta patrulla.")
        po.loc[mask, "estado"] = ESTADO_OFICIAL_REMOVIDO
        self.tx.write_table("app_patrulla_oficiales", po)
        self._touch_patrulla(int(fk_patrulla))
        return {"fk_patrulla": int(fk_patrulla), "fk_oficial": int(fk_oficial), "estado": ESTADO_OFICIAL_REMOVIDO}

    def set_patrulla_estado(self, fk_patrulla: int, estado: str) -> dict[str, Any]:
        if estado not in ESTADOS_PATRULLA:
            raise ValueError(f"Estado de patrulla inválido. Use: {ESTADOS_PATRULLA}")
        df = self.tx.read_table("app_patrullas")
        mask = df["id_patrulla"].astype(int) == int(fk_patrulla)
        if not mask.any():
            raise ValueError("Patrulla no encontrada.")
        df.loc[mask, "estado"] = estado
        df.loc[mask, "fecha_actualizacion"] = utc_now_iso()
        self.tx.write_table("app_patrullas", df)
        return _json_safe(df[mask].iloc[0].to_dict())

    def _touch_patrulla(self, fk_patrulla: int) -> None:
        df = self.tx.read_table("app_patrullas")
        mask = df["id_patrulla"].astype(int) == int(fk_patrulla)
        if mask.any():
            df.loc[mask, "fecha_actualizacion"] = utc_now_iso()
            self.tx.write_table("app_patrullas", df)

    def _patrulla_row(self, fk_patrulla: int) -> dict[str, Any] | None:
        df = self.tx.read_table("app_patrullas")
        row = df[df["id_patrulla"].astype(int) == int(fk_patrulla)]
        return row.iloc[0].to_dict() if not row.empty else None

    # ── Incidentes y despacho ──────────────────────────────────────────
    def list_incidentes(self, *, estado: str = "") -> list[dict[str, Any]]:
        df = self.tx.read_table("app_incidentes")
        if df.empty:
            return []
        if estado:
            df = df[df["estado"].astype(str) == estado]
        return [
            _json_safe(r)
            for r in df.sort_values("id_incidente", ascending=False).to_dict(orient="records")
        ]

    def create_incidente(
        self,
        *,
        operador: dict[str, Any],
        tipo: str,
        descripcion: str,
        ubicacion: str,
        prioridad: str = "Media",
        reportante: str = "",
    ) -> dict[str, Any]:
        if not str(ubicacion).strip():
            raise ValueError("La ubicación del incidente es obligatoria.")
        tipo = str(tipo).strip() or "Otro"
        if prioridad not in PRIORIDADES:
            prioridad = "Media"
        df = self.tx.read_table("app_incidentes")
        now = utc_now_iso()
        row = {
            "codigo": self._next_incidente_codigo(df),
            "tipo": tipo,
            "descripcion": str(descripcion or "").strip(),
            "ubicacion": str(ubicacion).strip(),
            "prioridad": prioridad,
            "estado": "Reportado",
            "reportante": str(reportante or "").strip(),
            "fk_patrulla": None,
            "patrulla_codigo": "",
            "fk_operador": int(operador["id_usuario"]),
            "operador_nombre": self._persona(operador),
            "fk_comisario": None,
            "comisario_nombre": "",
            "notas_despacho": "",
            "apoyo_solicitado": False,
            "resultado_atencion": "",
            "parte_policial": "",
            "motivo_devolucion": "",
            "fecha_reporte": now,
            "fecha_despacho": "",
            "fecha_atendido": "",
            "fecha_cierre": "",
        }
        created = self.tx.append_row("app_incidentes", row)
        return _json_safe(created)

    def dispatch(
        self,
        fk_incidente: int,
        *,
        fk_patrulla: int,
        comisario: dict[str, Any],
        prioridad: str = "",
        notas: str = "",
    ) -> dict[str, Any]:
        """CU-O78: el Comisario evalúa, define prioridad y despacha una patrulla al incidente."""
        inc_df = self.tx.read_table("app_incidentes")
        imask = inc_df["id_incidente"].astype(int) == int(fk_incidente)
        if not imask.any():
            raise ValueError("Incidente no encontrado.")
        incidente = inc_df[imask].iloc[0].to_dict()
        if str(incidente.get("estado")) != "Reportado":
            raise ValueError(
                f"Solo se puede despachar un incidente en estado «Reportado» "
                f"(estado actual: {incidente.get('estado')})."
            )

        patrulla = self._patrulla_row(int(fk_patrulla))
        if not patrulla:
            raise ValueError("Patrulla no encontrada.")
        if str(patrulla.get("estado")) != "Disponible":
            raise ValueError(
                f"La patrulla {patrulla.get('codigo')} no está disponible "
                f"(estado actual: {patrulla.get('estado')})."
            )
        # Debe tener al menos un oficial asignado (CU-O77 previo).
        po = self.tx.read_table("app_patrulla_oficiales")
        if not self._oficiales_de_patrulla(po, int(fk_patrulla)):
            raise ValueError("La patrulla no tiene oficiales asignados; asígnelos primero (CU-O77).")

        now = utc_now_iso()
        antes = {"incidente_estado": incidente.get("estado"), "patrulla_estado": patrulla.get("estado")}

        inc_df.loc[imask, "estado"] = "Despachado"
        if prioridad in PRIORIDADES:
            inc_df.loc[imask, "prioridad"] = prioridad
        inc_df.loc[imask, "fk_patrulla"] = int(fk_patrulla)
        inc_df.loc[imask, "patrulla_codigo"] = str(patrulla.get("codigo"))
        inc_df.loc[imask, "fk_comisario"] = int(comisario["id_usuario"])
        inc_df.loc[imask, "comisario_nombre"] = self._persona(comisario)
        inc_df.loc[imask, "notas_despacho"] = str(notas or "").strip()
        inc_df.loc[imask, "fecha_despacho"] = now
        self.tx.write_table("app_incidentes", inc_df)

        self.set_patrulla_estado(int(fk_patrulla), "Despachada")

        despues = {"incidente_estado": "Despachado", "patrulla_estado": "Despachada"}
        return {
            "incidente": _json_safe(inc_df[imask].iloc[0].to_dict()),
            "antes": antes,
            "despues": despues,
        }

    # ── Vista del Oficial que recibe ───────────────────────────────────
    def _patrulla_ids_de_oficial(self, fk_oficial: int) -> list[int]:
        po = self.tx.read_table("app_patrulla_oficiales")
        if po.empty:
            return []
        sub = po[
            (po["fk_oficial"].astype(int) == int(fk_oficial))
            & (po["estado"].astype(str) == ESTADO_OFICIAL_ACTIVO)
        ]
        return [int(x) for x in sub["fk_patrulla"].astype(int).unique()]

    def mis_patrullas(self, fk_oficial: int) -> list[dict[str, Any]]:
        ids = self._patrulla_ids_de_oficial(int(fk_oficial))
        if not ids:
            return []
        df = self.tx.read_table("app_patrullas")
        po = self.tx.read_table("app_patrulla_oficiales")
        out = []
        for row in df[df["id_patrulla"].astype(int).isin(ids)].to_dict(orient="records"):
            item = _json_safe(row)
            item["oficiales"] = self._oficiales_de_patrulla(po, int(row["id_patrulla"]))
            out.append(item)
        return out

    def mis_incidentes(self, fk_oficial: int) -> list[dict[str, Any]]:
        ids = self._patrulla_ids_de_oficial(int(fk_oficial))
        if not ids:
            return []
        df = self.tx.read_table("app_incidentes")
        if df.empty:
            return []
        sub = df[df["fk_patrulla"].isin(ids)]
        sub = sub[sub["estado"].astype(str) != "Cerrado"]
        return [
            _json_safe(r)
            for r in sub.sort_values("id_incidente", ascending=False).to_dict(orient="records")
        ]

    # Avance lineal del oficial receptor (incidente_estado → patrulla_estado).
    # El cierre NO está aquí: lo aprueba el Comisario (aprobar_cierre).
    _RECEPTOR_TRANSICIONES = {
        "Despachado": ("En camino", "En ruta"),
        "En camino": ("En el lugar", "En sitio"),
        "En el lugar": ("En atención", "En sitio"),
    }

    # ── Seed de demostración (idempotente) ─────────────────────────────
    def seed_demo(self) -> dict[str, Any]:
        """Crea patrullas/incidentes de ejemplo si aún no existen (datos operativos)."""
        patrullas = self.tx.read_table("app_patrullas")
        incidentes = self.tx.read_table("app_incidentes")
        if not patrullas.empty or not incidentes.empty:
            return {"patrullas": int(len(patrullas)), "incidentes": int(len(incidentes)), "creado": False}

        users = self._users_df()
        comisarios = users[users["fk_rol"].astype("Int64") == FK_ROL_COMISARIO] if not users.empty else users
        comisario = (
            comisarios.iloc[0].to_dict()
            if not comisarios.empty
            else {"id_usuario": 1, "nombres": "Sistema", "apellidos": ""}
        )
        oficiales = (
            users[users["fk_rol"].astype("Int64") == FK_ROL_OFICIAL].to_dict(orient="records")
            if not users.empty
            else []
        )

        p1 = self.create_patrulla(comisario=comisario, sector="Centro Histórico", turno="Diurno (06:00-14:00)", notas="Cobertura zona comercial")
        p2 = self.create_patrulla(comisario=comisario, sector="Zona Norte", turno="Nocturno (22:00-06:00)", notas="Patrullaje preventivo")
        if len(oficiales) >= 1:
            self.assign_oficiales(int(p1["id_patrulla"]), oficial_ids=[int(oficiales[0]["id_usuario"])], comisario=comisario)
        if len(oficiales) >= 3:
            self.assign_oficiales(int(p2["id_patrulla"]), oficial_ids=[int(oficiales[1]["id_usuario"]), int(oficiales[2]["id_usuario"])], comisario=comisario)

        self.create_incidente(
            operador=comisario,
            tipo="Robo",
            descripcion="Reporte de robo a local comercial",
            ubicacion="Av. Principal y Calle 5",
            prioridad="Alta",
            reportante="Ciudadano (línea 911)",
        )
        self.create_incidente(
            operador=comisario,
            tipo="Disturbio",
            descripcion="Riña en vía pública",
            ubicacion="Parque Central",
            prioridad="Media",
            reportante="Cámara de videovigilancia",
        )
        return {"patrullas": 2, "incidentes": 2, "creado": True}

    def _incidente_de_oficial(self, df: pd.DataFrame, fk_incidente: int, fk_oficial: int) -> tuple[Any, dict, int]:
        """Devuelve (mask, incidente, fk_patrulla) validando que el incidente pertenezca al oficial."""
        mask = df["id_incidente"].astype(int) == int(fk_incidente)
        if not mask.any():
            raise ValueError("Incidente no encontrado.")
        incidente = df[mask].iloc[0].to_dict()
        try:
            fk_patrulla = int(incidente.get("fk_patrulla"))
        except (TypeError, ValueError):
            raise ValueError("El incidente no tiene patrulla despachada.")
        if fk_patrulla not in self._patrulla_ids_de_oficial(int(fk_oficial)):
            raise ValueError("No pertenece a la patrulla asignada a este incidente.")
        return mask, incidente, fk_patrulla

    def _append_nota(self, incidente: dict, actor: dict, texto: str) -> str:
        prev = str(incidente.get("notas_despacho") or "")
        return (prev + f"\n[{utc_now_iso()}] {self._persona(actor)}: {texto}").strip()

    def avanzar_incidente(
        self,
        fk_incidente: int,
        *,
        oficial: dict[str, Any],
        nota: str = "",
    ) -> dict[str, Any]:
        """El oficial acepta/avanza el incidente: Despachado→En camino→En el lugar→En atención."""
        df = self.tx.read_table("app_incidentes")
        mask, incidente, fk_patrulla = self._incidente_de_oficial(
            df, int(fk_incidente), int(oficial["id_usuario"])
        )

        estado_actual = str(incidente.get("estado"))
        if estado_actual not in self._RECEPTOR_TRANSICIONES:
            raise ValueError(f"No hay transición disponible desde «{estado_actual}».")
        nuevo_estado_inc, nuevo_estado_pat = self._RECEPTOR_TRANSICIONES[estado_actual]

        antes = {"incidente_estado": estado_actual, "patrulla_estado": self._patrulla_row(fk_patrulla).get("estado")}
        df.loc[mask, "estado"] = nuevo_estado_inc
        if nota:
            df.loc[mask, "notas_despacho"] = self._append_nota(incidente, oficial, nota)
        self.tx.write_table("app_incidentes", df)
        self.set_patrulla_estado(fk_patrulla, nuevo_estado_pat)

        return {
            "incidente": _json_safe(df[mask].iloc[0].to_dict()),
            "antes": antes,
            "despues": {"incidente_estado": nuevo_estado_inc, "patrulla_estado": nuevo_estado_pat},
        }

    def finalizar_atencion(
        self,
        fk_incidente: int,
        *,
        oficial: dict[str, Any],
        resultado: str,
        parte: str = "",
    ) -> dict[str, Any]:
        """El oficial cierra su atención: En atención→Atendido, registra resultado y parte policial."""
        if not str(resultado).strip():
            raise ValueError("Debe registrar el resultado de la atención.")
        df = self.tx.read_table("app_incidentes")
        mask, incidente, _ = self._incidente_de_oficial(
            df, int(fk_incidente), int(oficial["id_usuario"])
        )
        if str(incidente.get("estado")) != "En atención":
            raise ValueError("Solo puede finalizar un incidente en estado «En atención».")

        now = utc_now_iso()
        antes = {"incidente_estado": "En atención"}
        df.loc[mask, "estado"] = "Atendido"
        df.loc[mask, "resultado_atencion"] = str(resultado).strip()
        df.loc[mask, "parte_policial"] = str(parte or "").strip() or self._parte_template(incidente, resultado, oficial)
        df.loc[mask, "fecha_atendido"] = now
        self.tx.write_table("app_incidentes", df)
        # La patrulla sigue ocupada (En sitio) hasta que el Comisario apruebe el cierre.

        return {
            "incidente": _json_safe(df[mask].iloc[0].to_dict()),
            "antes": antes,
            "despues": {"incidente_estado": "Atendido"},
        }

    def solicitar_apoyo(
        self,
        fk_incidente: int,
        *,
        oficial: dict[str, Any],
        nota: str = "",
    ) -> dict[str, Any]:
        """El oficial solicita apoyo operativo (no cambia el estado del incidente)."""
        df = self.tx.read_table("app_incidentes")
        mask, incidente, _ = self._incidente_de_oficial(
            df, int(fk_incidente), int(oficial["id_usuario"])
        )
        df.loc[mask, "apoyo_solicitado"] = True
        df.loc[mask, "notas_despacho"] = self._append_nota(
            incidente, oficial, f"APOYO SOLICITADO. {nota}".strip()
        )
        self.tx.write_table("app_incidentes", df)
        return {"incidente": _json_safe(df[mask].iloc[0].to_dict())}

    def aprobar_cierre(
        self,
        fk_incidente: int,
        *,
        comisario: dict[str, Any],
    ) -> dict[str, Any]:
        """El Comisario revisa el parte y aprueba el cierre: Atendido→Cerrado; libera la patrulla."""
        df = self.tx.read_table("app_incidentes")
        mask = df["id_incidente"].astype(int) == int(fk_incidente)
        if not mask.any():
            raise ValueError("Incidente no encontrado.")
        incidente = df[mask].iloc[0].to_dict()
        if str(incidente.get("estado")) != "Atendido":
            raise ValueError("Solo se puede cerrar un incidente en estado «Atendido».")

        now = utc_now_iso()
        antes = {"incidente_estado": "Atendido"}
        df.loc[mask, "estado"] = "Cerrado"
        df.loc[mask, "fecha_cierre"] = now
        self.tx.write_table("app_incidentes", df)

        try:
            fk_patrulla = int(incidente.get("fk_patrulla"))
            self.set_patrulla_estado(fk_patrulla, "Disponible")
        except (TypeError, ValueError):
            pass

        return {
            "incidente": _json_safe(df[mask].iloc[0].to_dict()),
            "antes": antes,
            "despues": {"incidente_estado": "Cerrado", "patrulla_estado": "Disponible"},
        }

    def devolver_incidente(
        self,
        fk_incidente: int,
        *,
        comisario: dict[str, Any],
        motivo: str,
    ) -> dict[str, Any]:
        """El Comisario devuelve el caso para corrección: Atendido→En atención (con motivo)."""
        if not str(motivo).strip():
            raise ValueError("Indique el motivo de la devolución.")
        df = self.tx.read_table("app_incidentes")
        mask = df["id_incidente"].astype(int) == int(fk_incidente)
        if not mask.any():
            raise ValueError("Incidente no encontrado.")
        incidente = df[mask].iloc[0].to_dict()
        if str(incidente.get("estado")) != "Atendido":
            raise ValueError("Solo se puede devolver un incidente en estado «Atendido».")

        antes = {"incidente_estado": "Atendido"}
        df.loc[mask, "estado"] = "En atención"
        df.loc[mask, "motivo_devolucion"] = str(motivo).strip()
        df.loc[mask, "notas_despacho"] = self._append_nota(
            incidente, comisario, f"DEVUELTO PARA CORRECCIÓN: {motivo}"
        )
        self.tx.write_table("app_incidentes", df)
        return {
            "incidente": _json_safe(df[mask].iloc[0].to_dict()),
            "antes": antes,
            "despues": {"incidente_estado": "En atención"},
        }

    @staticmethod
    def _parte_template(incidente: dict, resultado: str, oficial: dict) -> str:
        return (
            f"PARTE POLICIAL — Incidente {incidente.get('codigo')}\n"
            f"Tipo: {incidente.get('tipo')} | Prioridad: {incidente.get('prioridad')}\n"
            f"Ubicación: {incidente.get('ubicacion')}\n"
            f"Oficial a cargo: {oficial.get('nombres', '')} {oficial.get('apellidos', '')}\n"
            f"Resultado de la atención: {resultado}"
        )
