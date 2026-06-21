from __future__ import annotations

from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore
from packages.asignacion_investigaciones.services.casos_operativos_store import (
    CasosOperativosStore,
)
from packages.asignacion_investigaciones.services.notifications import (
    send_assignment_notification,
)
from packages.autenticacion_seguridad.services.auth_service import AuthService
from packages.autenticacion_seguridad.services.seed import FK_ROL_DETECTIVE
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

ESTADO_ACTIVA = "Activa"
ESTADO_REASIGNADA = "Reasignada"
ESTADO_REMOVIDA = "Removida"
MAX_CASOS_RECOMENDADOS = 15


class AssignmentService:
    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()
        self.olap = MinioParquetStore()
        self.casos = CasosOperativosStore()
        self.tx.ensure_tables()

    def _asignaciones_df(self) -> pd.DataFrame:
        return self.tx.read_table("app_asignaciones")

    def _users_df(self) -> pd.DataFrame:
        return AuthService._normalize_users_df(self.tx.read_table("app_usuarios"))

    @staticmethod
    def _detective_label(row: dict) -> str:
        return (
            f"Det. {row.get('apellidos', '')}, {row.get('nombres', '')} "
            f"({row.get('numero_placa', '')})"
        ).strip()

    def _comisario_display(self, user: dict) -> str:
        return f"{user.get('apellidos', '')}, {user.get('nombres', '')}".strip()

    @staticmethod
    def _refresh_dashboard_ranking() -> None:
        try:
            from packages.dashboard_analitica.services.summary_materializer import (
                refresh_investigation_dashboard_metrics,
            )

            refresh_investigation_dashboard_metrics()
        except Exception:
            pass

    def _active_assignments(self) -> pd.DataFrame:
        df = self._asignaciones_df()
        if df.empty:
            return df
        return df[df["estado_asignacion"].astype(str) == ESTADO_ACTIVA]

    def list_detectives_workload(self) -> list[dict[str, Any]]:
        users = self._users_df()
        detectives = users[users["fk_rol"] == FK_ROL_DETECTIVE]
        if detectives.empty:
            return []

        active = self._active_assignments()
        counts: dict[int, int] = {}
        if not active.empty:
            for fk in active["fk_detective"].astype(int):
                counts[int(fk)] = counts.get(int(fk), 0) + 1

        items = []
        for row in detectives.to_dict(orient="records"):
            uid = int(row["id_usuario"])
            casos = counts.get(uid, 0)
            items.append(
                {
                    "id_usuario": uid,
                    "nombres": row["nombres"],
                    "apellidos": row["apellidos"],
                    "email": row["email"],
                    "numero_placa": row["numero_placa"],
                    "estado_cuenta": row["estado_cuenta"],
                    "casos_activos": casos,
                    "carga_pct": min(100, round(100 * casos / MAX_CASOS_RECOMENDADOS)),
                    "disponible": casos < MAX_CASOS_RECOMENDADOS
                    and str(row["estado_cuenta"]).lower() == "activa",
                    "etiqueta": self._detective_label(row),
                }
            )
        items.sort(key=lambda x: (not x["disponible"], x["casos_activos"], x["apellidos"]))
        return items

    def list_casos(
        self,
        *,
        q: str = "",
        page: int = 1,
        per_page: int = 40,
        solo_sin_asignar: bool = False,
        solo_asignados: bool = False,
        estado: str = "",
        prioridad: str = "",
    ) -> dict[str, Any]:
        return self.casos.search_casos(
            q=q,
            page=page,
            per_page=per_page,
            solo_sin_asignar=solo_sin_asignar,
            solo_asignados=solo_asignados,
            estado=estado,
            prioridad=prioridad,
        )

    def _get_caso(self, fk_caso: int) -> dict | None:
        return self.casos.get_caso_by_id(fk_caso)

    def _get_detective(self, fk_detective: int) -> dict | None:
        users = self._users_df()
        row = users[users["id_usuario"].astype(int) == fk_detective]
        if row.empty or int(row.iloc[0]["fk_rol"]) != FK_ROL_DETECTIVE:
            return None
        return row.iloc[0].to_dict()

    def _sync_dim_caso_investigador(self, fk_caso: int, label: str | None) -> None:
        try:
            self.olap.update_record(
                "dim_caso",
                str(fk_caso),
                {"investigador_asignado": label or ""},
            )
        except Exception:
            pass

    def _cerrar_asignacion_activa(
        self,
        fk_caso: int,
        *,
        nuevo_estado: str,
        motivo: str,
    ) -> None:
        df = self._asignaciones_df()
        if df.empty:
            return
        mask = (df["fk_caso"].astype(int) == fk_caso) & (
            df["estado_asignacion"].astype(str) == ESTADO_ACTIVA
        )
        if not mask.any():
            return
        now = utc_now_iso()
        df.loc[mask, "estado_asignacion"] = nuevo_estado
        df.loc[mask, "fecha_cierre"] = now
        df.loc[mask, "motivo_cierre"] = motivo
        self.tx.write_table("app_asignaciones", df)

    def _audit(self, fk_usuario: int, accion: str, detalle: str) -> None:
        self.tx.append_row(
            "app_audit_logs",
            {
                "fk_usuario": fk_usuario,
                "accion": accion,
                "tabla_afectada": "app_asignaciones",
                "detalle": detalle,
                "direccion_ip": "",
                "fecha_hora": utc_now_iso(),
            },
        )

    @staticmethod
    def _caso_snapshots(caso: dict) -> dict[str, str]:
        return {
            "estado_caso_snapshot": str(caso.get("estado_caso") or ""),
            "prioridad_caso_snapshot": str(caso.get("prioridad_caso") or ""),
            "fecha_reporte_snapshot": str(caso.get("fecha_reporte") or ""),
            "observaciones_caso_snapshot": str(caso.get("observaciones") or ""),
        }

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        if value is None:
            return default
        try:
            if pd.isna(value):
                return default
        except (TypeError, ValueError):
            pass
        try:
            return max(0, min(100, int(float(value))))
        except (TypeError, ValueError):
            return default

    def _latest_bitacora_by_case(self) -> dict[str, dict[str, Any]]:
        """Última entrada de bitácora por case_number (mayúsculas)."""
        df = self.tx.read_table("app_expediente_bitacora")
        if df.empty:
            return {}
        sorted_df = df.sort_values("fecha_hora", ascending=False)
        out: dict[str, dict[str, Any]] = {}
        for row in sorted_df.to_dict(orient="records"):
            cn = str(row.get("case_number") or "").strip().upper()
            if cn and cn not in out:
                out[cn] = row
        return out

    @classmethod
    def _resolve_avance(
        cls,
        asig: dict[str, Any],
        *,
        bitacora_row: dict[str, Any] | None = None,
    ) -> int:
        if bitacora_row is not None:
            avance = cls._safe_int(bitacora_row.get("avance_pct"), default=-1)
            if avance >= 0:
                return avance
        stored = cls._safe_int(asig.get("avance_pct_actual"), default=-1)
        if stored >= 0 and not pd.isna(asig.get("avance_pct_actual")):
            return stored
        estado = str(
            (bitacora_row or {}).get("estado_caso")
            or asig.get("estado_caso_snapshot")
            or asig.get("estado_caso")
            or ""
        )
        return cls._avance_por_estado(estado)

    def assign_detective(
        self,
        *,
        fk_caso: int,
        fk_detective: int,
        comisario: dict[str, Any],
        observaciones: str = "",
    ) -> dict[str, Any]:
        caso = self._get_caso(fk_caso)
        if not caso:
            raise ValueError("Caso no encontrado en dim_caso")

        detective = self._get_detective(fk_detective)
        if not detective:
            raise ValueError("Detective no válido o inactivo")

        if str(detective.get("estado_cuenta", "")).lower() != "activa":
            raise ValueError("La cuenta del detective no está activa")

        workload = self.list_detectives_workload()
        det_info = next((d for d in workload if d["id_usuario"] == fk_detective), None)
        if det_info and not det_info["disponible"]:
            raise ValueError(
                f"El detective tiene {det_info['casos_activos']} casos activos "
                f"(máximo recomendado {MAX_CASOS_RECOMENDADOS})"
            )

        self._cerrar_asignacion_activa(
            fk_caso,
            nuevo_estado=ESTADO_REASIGNADA,
            motivo="Reasignación de detective",
        )

        now = utc_now_iso()
        label = self._detective_label(detective)
        comisario_nombre = self._comisario_display(comisario)
        row = {
            "fk_caso": fk_caso,
            "case_number": str(caso.get("case_number", "")),
            "fk_detective": fk_detective,
            "detective_nombre": label,
            "detective_placa": detective["numero_placa"],
            "fk_comisario": int(comisario["id_usuario"]),
            "comisario_nombre": comisario_nombre,
            "fecha_asignacion": now,
            "estado_asignacion": ESTADO_ACTIVA,
            "notificado": False,
            "fecha_notificacion": "",
            "observaciones": observaciones or "",
            "fecha_cierre": "",
            "motivo_cierre": "",
            "avance_pct_actual": self._avance_por_estado("En investigación"),
            **self._caso_snapshots(caso),
            "estado_caso_snapshot": "En investigación",
        }
        created = self.tx.append_row("app_asignaciones", row)

        self._sync_dim_caso_investigador(fk_caso, label)
        try:
            self.olap.update_record(
                "dim_caso",
                str(fk_caso),
                {"estado_caso": "En investigación"},
            )
        except Exception:
            pass

        notified = send_assignment_notification(
            to_email=str(detective["email"]),
            detective_nombre=f"{detective['nombres']} {detective['apellidos']}",
            case_number=str(caso.get("case_number", "")),
            comisario_nombre=comisario_nombre,
            fecha_asignacion=now,
        )
        if notified:
            df = self._asignaciones_df()
            mask = df["id_asignacion"].astype(int) == int(created["id_asignacion"])
            df.loc[mask, "notificado"] = True
            df.loc[mask, "fecha_notificacion"] = utc_now_iso()
            self.tx.write_table("app_asignaciones", df)
            created["notificado"] = True

        self._audit(
            int(comisario["id_usuario"]),
            "ASIGNAR_DETECTIVE",
            f"{comisario_nombre} asignó el caso {caso.get('case_number')} al detective {label}",
        )
        self._refresh_dashboard_ranking()
        return self._public_assignment(created)

    def reassign_detective(
        self,
        *,
        fk_caso: int,
        fk_detective: int,
        comisario: dict[str, Any],
        observaciones: str = "",
    ) -> dict[str, Any]:
        return self.assign_detective(
            fk_caso=fk_caso,
            fk_detective=fk_detective,
            comisario=comisario,
            observaciones=observaciones or "Reasignación solicitada por Comisario",
        )

    def remove_detective(
        self,
        *,
        fk_caso: int,
        comisario: dict[str, Any],
        motivo: str = "",
    ) -> dict[str, Any]:
        caso = self._get_caso(fk_caso)
        if not caso:
            raise ValueError("Caso no encontrado")

        self._cerrar_asignacion_activa(
            fk_caso,
            nuevo_estado=ESTADO_REMOVIDA,
            motivo=motivo or "Removido por Comisario",
        )
        self._sync_dim_caso_investigador(fk_caso, None)
        self._audit(
            int(comisario["id_usuario"]),
            "REMOVER_DETECTIVE",
            f"{self._comisario_display(comisario)} removió al detective del caso {caso.get('case_number')}",
        )
        self._refresh_dashboard_ranking()
        return {"fk_caso": fk_caso, "case_number": caso.get("case_number"), "estado": ESTADO_REMOVIDA}

    def investigation_progress(
        self,
        *,
        user: dict[str, Any],
        solo_mis_casos: bool = False,
    ) -> dict[str, Any]:
        """Solo lee app_asignaciones (sin escanear dim_caso)."""
        role = str(user.get("nombre_rol", "")).lower()
        fk_user = int(user["id_usuario"])

        active = self._active_assignments()
        if active.empty:
            return {"items": [], "resumen": {"total": 0, "en_investigacion": 0}}

        if solo_mis_casos or role == "detective":
            active = active[active["fk_detective"].astype(int) == fk_user]

        bitacora_by_case = self._latest_bitacora_by_case()
        items = []
        en_inv = 0
        for asig in active.to_dict(orient="records"):
            cn = str(asig.get("case_number") or "").strip().upper()
            bitacora = bitacora_by_case.get(cn)
            estado = str(
                (bitacora or {}).get("estado_caso")
                or asig.get("estado_caso_snapshot")
                or asig.get("estado_caso")
                or "En investigación"
            )
            if estado.lower() == "en investigación":
                en_inv += 1
            items.append(
                {
                    "id_asignacion": int(asig["id_asignacion"]),
                    "fk_caso": int(asig["fk_caso"]),
                    "case_number": asig.get("case_number"),
                    "detective_nombre": asig.get("detective_nombre"),
                    "detective_placa": asig.get("detective_placa"),
                    "fecha_asignacion": asig.get("fecha_asignacion"),
                    "notificado": bool(asig.get("notificado")),
                    "estado_caso": estado,
                    "prioridad_caso": asig.get("prioridad_caso_snapshot")
                    or asig.get("prioridad_caso"),
                    "fecha_reporte": asig.get("fecha_reporte_snapshot"),
                    "observaciones": asig.get("observaciones_caso_snapshot")
                    or asig.get("observaciones"),
                    "avance_pct": self._resolve_avance(asig, bitacora_row=bitacora),
                }
            )

        return {
            "items": items,
            "resumen": {
                "total": len(items),
                "en_investigacion": en_inv,
            },
        }

    @staticmethod
    def _avance_por_estado(estado: str) -> int:
        mapping = {
            "abierto": 15,
            "en investigación": 55,
            "cerrado": 90,
            "archivado": 100,
        }
        return mapping.get(estado.lower().strip(), 30)

    @staticmethod
    def _public_assignment(row: dict) -> dict[str, Any]:
        return {
            "id_asignacion": int(row["id_asignacion"]),
            "fk_caso": int(row["fk_caso"]),
            "case_number": row.get("case_number"),
            "fk_detective": int(row["fk_detective"]),
            "detective_nombre": row.get("detective_nombre"),
            "fecha_asignacion": row.get("fecha_asignacion"),
            "estado_asignacion": row.get("estado_asignacion"),
            "notificado": bool(row.get("notificado")),
            "observaciones": row.get("observaciones"),
        }
