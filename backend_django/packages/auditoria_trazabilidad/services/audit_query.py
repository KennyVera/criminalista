"""
Servicio de consulta de auditoría (P03 — CU-O12, CU-O73, CU-O74).

Lee ``app_audit_logs`` (Parquet en MinIO), enriquece cada evento con datos del
usuario/rol, clasifica acción/categoría/severidad/resultado, aplica filtros
avanzados, pagina y calcula estadísticas. Provee exportación CSV autorizada.
"""

from __future__ import annotations

import csv
import io
import math
from typing import Any

import pandas as pd

from packages.shared.minio_transactional import TransactionalMinioStore

# ── Catálogo de acciones → etiqueta legible, categoría, severidad y resultado ──
# severidad: critico | alto | medio | info   ·   resultado: exito | fallo | info
ACTION_META: dict[str, dict[str, str]] = {
    "LOGIN": {"label": "Inicio de sesión", "categoria": "Autenticación", "severidad": "info", "resultado": "exito"},
    "LOGOUT": {"label": "Cierre de sesión", "categoria": "Sesiones", "severidad": "info", "resultado": "exito"},
    "LOGIN_FAILED": {"label": "Inicio de sesión fallido", "categoria": "Autenticación", "severidad": "alto", "resultado": "fallo"},
    "ACCOUNT_LOCKED": {"label": "Cuenta bloqueada", "categoria": "Autenticación", "severidad": "critico", "resultado": "fallo"},
    "SESSION_CLOSED_BY_ADMIN": {"label": "Sesión cerrada por admin", "categoria": "Sesiones", "severidad": "medio", "resultado": "exito"},
    "PASSWORD_RESET_REQUEST": {"label": "Solicitud de recuperación", "categoria": "Autenticación", "severidad": "medio", "resultado": "exito"},
    "PASSWORD_RESET_OK": {"label": "Contraseña restablecida", "categoria": "Autenticación", "severidad": "medio", "resultado": "exito"},
    "MFA_CODE_SENT": {"label": "Código 2FA enviado", "categoria": "Autenticación", "severidad": "info", "resultado": "exito"},
    "MFA_VERIFIED": {"label": "Segundo factor verificado", "categoria": "Autenticación", "severidad": "info", "resultado": "exito"},
    "MFA_FAILED": {"label": "Código 2FA incorrecto", "categoria": "Autenticación", "severidad": "alto", "resultado": "fallo"},
    "ASIGNAR_DETECTIVE": {"label": "Asignación de detective", "categoria": "Asignaciones", "severidad": "info", "resultado": "exito"},
    "REMOVER_DETECTIVE": {"label": "Remoción de detective", "categoria": "Asignaciones", "severidad": "medio", "resultado": "exito"},
    # Operación de campo — expedientes / detectives (CU-O)
    "INVOLUCRADO_ADDED": {"label": "Involucrado/testigo agregado", "categoria": "Involucrados", "severidad": "info", "resultado": "exito"},
    "EVIDENCE_UPLOADED": {"label": "Evidencia cargada", "categoria": "Evidencias", "severidad": "medio", "resultado": "exito"},
    "EVIDENCE_CUSTODY_CHANGED": {"label": "Cambio de custodia de evidencia", "categoria": "Evidencias", "severidad": "medio", "resultado": "exito"},
    "CASE_UPDATED": {"label": "Actualización de expediente", "categoria": "Expedientes", "severidad": "info", "resultado": "exito"},
    "CASE_PDF_EXPORTED": {"label": "Informe PDF exportado", "categoria": "Exportación", "severidad": "medio", "resultado": "exito"},
    "REPORT_SENT": {"label": "Reporte enviado por correo", "categoria": "Reportes", "severidad": "medio", "resultado": "exito"},
    "REPORT_SCHEDULE_CREATED": {"label": "Reporte programado", "categoria": "Reportes", "severidad": "info", "resultado": "exito"},
    "REPORT_SCHEDULE_UPDATED": {"label": "Programación de reporte modificada", "categoria": "Reportes", "severidad": "info", "resultado": "exito"},
    "REPORT_SCHEDULE_DELETED": {"label": "Programación de reporte eliminada", "categoria": "Reportes", "severidad": "medio", "resultado": "exito"},
    "INTEGRITY_ALERT": {"label": "Alerta de integridad", "categoria": "Seguridad", "severidad": "critico", "resultado": "fallo"},
    "INTEGRITY_VERIFIED": {"label": "Verificación de integridad", "categoria": "Seguridad", "severidad": "info", "resultado": "exito"},
    "PATROL_CREATED": {"label": "Patrulla creada", "categoria": "Patrullas", "severidad": "info", "resultado": "exito"},
    "PATROL_ASSIGNED": {"label": "Oficiales asignados a patrulla", "categoria": "Patrullas", "severidad": "medio", "resultado": "exito"},
    "PATROL_OFFICER_REMOVED": {"label": "Oficial removido de patrulla", "categoria": "Patrullas", "severidad": "medio", "resultado": "exito"},
    "INCIDENT_REPORTED": {"label": "Incidente reportado", "categoria": "Patrullas", "severidad": "info", "resultado": "exito"},
    "PATROL_DISPATCHED": {"label": "Patrulla despachada a incidente", "categoria": "Patrullas", "severidad": "medio", "resultado": "exito"},
    "INCIDENT_STATUS_UPDATED": {"label": "Estado de incidente actualizado", "categoria": "Patrullas", "severidad": "info", "resultado": "exito"},
    "INCIDENT_RESOLVED": {"label": "Atención finalizada (parte generado)", "categoria": "Patrullas", "severidad": "info", "resultado": "exito"},
    "INCIDENT_CLOSED": {"label": "Cierre de incidente aprobado", "categoria": "Patrullas", "severidad": "medio", "resultado": "exito"},
    "INCIDENT_RETURNED": {"label": "Incidente devuelto para corrección", "categoria": "Patrullas", "severidad": "medio", "resultado": "exito"},
    "SUPPORT_REQUESTED": {"label": "Apoyo operativo solicitado", "categoria": "Patrullas", "severidad": "medio", "resultado": "exito"},
    "SEED_AUTH": {"label": "Carga inicial (auth)", "categoria": "Sistema", "severidad": "medio", "resultado": "info"},
    "SEED_ADMIN": {"label": "Carga inicial (admin)", "categoria": "Sistema", "severidad": "medio", "resultado": "info"},
    "BACKUP_RESTORE": {"label": "Restauración de respaldo", "categoria": "Continuidad", "severidad": "alto", "resultado": "exito"},
    "BACKUP_FAILED": {"label": "Respaldo fallido", "categoria": "Continuidad", "severidad": "critico", "resultado": "fallo"},
    # CRUD administrativo (CU-O61 / CU-O63 / CU-O69)
    "USER_CREATED": {"label": "Usuario creado", "categoria": "Gestión de usuarios", "severidad": "medio", "resultado": "exito"},
    "USER_UPDATED": {"label": "Usuario modificado", "categoria": "Gestión de usuarios", "severidad": "medio", "resultado": "exito"},
    "USER_DELETED": {"label": "Usuario eliminado", "categoria": "Gestión de usuarios", "severidad": "alto", "resultado": "exito"},
    "USER_STATUS_CHANGED": {"label": "Estado de cuenta cambiado", "categoria": "Gestión de usuarios", "severidad": "medio", "resultado": "exito"},
    "ROLE_PERMISSIONS_UPDATED": {"label": "Permisos de rol modificados", "categoria": "Roles y permisos", "severidad": "alto", "resultado": "exito"},
    "POLICY_UPDATED": {"label": "Política de seguridad modificada", "categoria": "Configuración", "severidad": "alto", "resultado": "exito"},
    "PARAM_UPDATED": {"label": "Parámetro modificado", "categoria": "Configuración", "severidad": "medio", "resultado": "exito"},
    "PARAM_CREATED": {"label": "Parámetro creado", "categoria": "Configuración", "severidad": "medio", "resultado": "exito"},
    "CATALOG_CREATED": {"label": "Catálogo creado", "categoria": "Configuración", "severidad": "info", "resultado": "exito"},
    "CATALOG_UPDATED": {"label": "Catálogo modificado", "categoria": "Configuración", "severidad": "info", "resultado": "exito"},
    "CATALOG_DELETED": {"label": "Catálogo eliminado", "categoria": "Configuración", "severidad": "medio", "resultado": "exito"},
    "ZONE_CREATED": {"label": "Zona creada", "categoria": "Configuración", "severidad": "info", "resultado": "exito"},
    "ZONE_UPDATED": {"label": "Zona modificada", "categoria": "Configuración", "severidad": "info", "resultado": "exito"},
    "ZONE_DELETED": {"label": "Zona eliminada", "categoria": "Configuración", "severidad": "medio", "resultado": "exito"},
    # CRUD sobre tablas/datasets genéricos (Explorar tablas)
    "RECORD_CREATED": {"label": "Registro creado", "categoria": "Datos y tablas", "severidad": "info", "resultado": "exito"},
    "RECORD_UPDATED": {"label": "Registro modificado", "categoria": "Datos y tablas", "severidad": "info", "resultado": "exito"},
    "RECORD_DELETED": {"label": "Registro eliminado", "categoria": "Datos y tablas", "severidad": "medio", "resultado": "exito"},
    # Exportaciones / reportes de auditoría (CU-O68 / CU-O74)
    "AUDIT_EXPORTED": {"label": "Auditoría exportada", "categoria": "Exportación", "severidad": "medio", "resultado": "exito"},
    "DATA_EXPORT": {"label": "Exportación de datos", "categoria": "Exportación", "severidad": "medio", "resultado": "exito"},
}

DEFAULT_META = {"label": "", "categoria": "Operación", "severidad": "info", "resultado": "info"}

# Operación (CRUD legible) derivada de cada acción — complementa la categoría.
# valores: creacion | modificacion | eliminacion | consulta | seguridad
OPERACION_BY_ACTION: dict[str, str] = {
    "LOGIN": "seguridad",
    "LOGOUT": "seguridad",
    "LOGIN_FAILED": "seguridad",
    "MFA_CODE_SENT": "seguridad",
    "MFA_VERIFIED": "seguridad",
    "MFA_FAILED": "seguridad",
    "ACCOUNT_LOCKED": "seguridad",
    "SESSION_CLOSED_BY_ADMIN": "seguridad",
    "PASSWORD_RESET_REQUEST": "seguridad",
    "PASSWORD_RESET_OK": "seguridad",
    "BACKUP_FAILED": "seguridad",
    "RECORD_CREATED": "creacion",
    "RECORD_UPDATED": "modificacion",
    "RECORD_DELETED": "eliminacion",
    "USER_CREATED": "creacion",
    "PARAM_CREATED": "creacion",
    "CATALOG_CREATED": "creacion",
    "ZONE_CREATED": "creacion",
    "INVOLUCRADO_ADDED": "creacion",
    "EVIDENCE_UPLOADED": "creacion",
    "EVIDENCE_CUSTODY_CHANGED": "modificacion",
    "ASIGNAR_DETECTIVE": "creacion",
    "SEED_AUTH": "creacion",
    "SEED_ADMIN": "creacion",
    "USER_UPDATED": "modificacion",
    "USER_STATUS_CHANGED": "modificacion",
    "ROLE_PERMISSIONS_UPDATED": "modificacion",
    "POLICY_UPDATED": "modificacion",
    "PARAM_UPDATED": "modificacion",
    "CATALOG_UPDATED": "modificacion",
    "ZONE_UPDATED": "modificacion",
    "CASE_UPDATED": "modificacion",
    "BACKUP_RESTORE": "modificacion",
    "USER_DELETED": "eliminacion",
    "CATALOG_DELETED": "eliminacion",
    "ZONE_DELETED": "eliminacion",
    "REMOVER_DETECTIVE": "eliminacion",
    "AUDIT_EXPORTED": "consulta",
    "DATA_EXPORT": "consulta",
    "CASE_PDF_EXPORTED": "consulta",
    "REPORT_SENT": "consulta",
    "REPORT_SCHEDULE_CREATED": "creacion",
    "REPORT_SCHEDULE_UPDATED": "modificacion",
    "REPORT_SCHEDULE_DELETED": "eliminacion",
    "INTEGRITY_ALERT": "seguridad",
    "INTEGRITY_VERIFIED": "seguridad",
    "PATROL_CREATED": "creacion",
    "PATROL_ASSIGNED": "creacion",
    "PATROL_OFFICER_REMOVED": "eliminacion",
    "INCIDENT_REPORTED": "creacion",
    "PATROL_DISPATCHED": "modificacion",
    "INCIDENT_STATUS_UPDATED": "modificacion",
    "INCIDENT_RESOLVED": "modificacion",
    "INCIDENT_CLOSED": "modificacion",
    "INCIDENT_RETURNED": "modificacion",
    "SUPPORT_REQUESTED": "seguridad",
}


def _operacion_for(accion: str) -> str:
    fixed = OPERACION_BY_ACTION.get(accion)
    if fixed:
        return fixed
    u = str(accion).upper()
    if any(k in u for k in ("DELETE", "DELETED", "REMOV", "DROP")):
        return "eliminacion"
    if any(k in u for k in ("CREATE", "CREATED", "ADDED", "UPLOAD", "ASIGN", "SEED", "NEW")):
        return "creacion"
    if any(k in u for k in ("UPDATE", "UPDATED", "CHANGED", "EDIT", "RESTORE", "PATCH")):
        return "modificacion"
    if any(k in u for k in ("LOGIN", "LOGOUT", "SESSION", "PASSWORD", "LOCK", "FAILED", "DENIED", "AUTH")):
        return "seguridad"
    if any(k in u for k in ("EXPORT", "PDF", "DOWNLOAD", "VIEW", "READ", "REPORT")):
        return "consulta"
    return "consulta"


def _clean_str(value) -> str:
    """Normaliza un valor de celda Parquet a cadena (vacía si es NaN/None)."""
    try:
        if value is None or pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _meta_for(accion: str) -> dict[str, str]:
    meta = ACTION_META.get(accion)
    if meta:
        return meta
    # Heurística para acciones no catalogadas.
    upper = str(accion).upper()
    resultado = "fallo" if any(k in upper for k in ("FAILED", "DENIED", "ERROR", "BLOCKED")) else "info"
    severidad = "alto" if resultado == "fallo" else "info"
    label = str(accion).replace("_", " ").capitalize()
    return {"label": label, "categoria": "Operación", "severidad": severidad, "resultado": resultado}


class AuditQueryService:
    def __init__(self) -> None:
        self.store = TransactionalMinioStore()

    # ── Mapas de enriquecimiento ──
    def _users_map(self) -> dict[int, dict[str, Any]]:
        try:
            df = self.store.read_table("app_usuarios")
        except Exception:
            return {}
        if df.empty:
            return {}
        roles = self._roles_map()
        out: dict[int, dict[str, Any]] = {}
        for r in df.to_dict(orient="records"):
            try:
                uid = int(r["id_usuario"])
            except (TypeError, ValueError, KeyError):
                continue
            fk_rol = r.get("fk_rol")
            try:
                fk_rol = int(fk_rol) if fk_rol is not None and not pd.isna(fk_rol) else None
            except (TypeError, ValueError):
                fk_rol = None
            nombres = str(r.get("nombres") or "").strip()
            apellidos = str(r.get("apellidos") or "").strip()
            out[uid] = {
                "nombre": f"{nombres} {apellidos}".strip(),
                "email": str(r.get("email") or ""),
                "rol": roles.get(fk_rol, "") if fk_rol is not None else "",
                "placa": str(r.get("numero_placa") or ""),
            }
        return out

    def _roles_map(self) -> dict[int, str]:
        try:
            df = self.store.read_table("app_roles")
        except Exception:
            return {}
        if df.empty:
            return {}
        out: dict[int, str] = {}
        for r in df.to_dict(orient="records"):
            try:
                out[int(r["id_rol"])] = str(r.get("nombre_rol") or "")
            except (TypeError, ValueError, KeyError):
                continue
        return out

    # ── Carga + enriquecimiento de todos los eventos ──
    def _load_enriched(self) -> list[dict[str, Any]]:
        try:
            df = self.store.read_table("app_audit_logs")
        except Exception:
            return []
        if df.empty:
            return []
        users = self._users_map()
        events: list[dict[str, Any]] = []
        for r in df.to_dict(orient="records"):
            raw_fk = r.get("fk_usuario")
            try:
                fk = int(raw_fk) if raw_fk is not None and not pd.isna(raw_fk) else None
            except (TypeError, ValueError):
                fk = None
            accion = str(r.get("accion") or "")
            meta = _meta_for(accion)
            uinfo = users.get(fk, {}) if fk is not None else {}
            try:
                id_log = int(r.get("id_log")) if r.get("id_log") is not None and not pd.isna(r.get("id_log")) else None
            except (TypeError, ValueError):
                id_log = None
            events.append(
                {
                    "id_log": id_log,
                    "fecha_hora": str(r.get("fecha_hora") or ""),
                    "fk_usuario": fk,
                    "usuario": uinfo.get("nombre") or ("Sistema" if fk is None else f"Usuario #{fk}"),
                    "email": uinfo.get("email", ""),
                    "rol": uinfo.get("rol", ""),
                    "placa": uinfo.get("placa", ""),
                    "accion": accion,
                    "accion_label": meta["label"] or accion,
                    "categoria": meta["categoria"],
                    "operacion": _operacion_for(accion),
                    "severidad": meta["severidad"],
                    "resultado": meta["resultado"],
                    "tabla_afectada": str(r.get("tabla_afectada") or ""),
                    "detalle": str(r.get("detalle") or ""),
                    "datos_anteriores": _clean_str(r.get("datos_anteriores")),
                    "datos_nuevos": _clean_str(r.get("datos_nuevos")),
                    "direccion_ip": str(r.get("direccion_ip") or ""),
                }
            )
        # Orden descendente por fecha (más reciente primero); fallback por id.
        events.sort(key=lambda e: (e["fecha_hora"], e["id_log"] or 0), reverse=True)
        return events

    # ── Filtrado ──
    @staticmethod
    def _apply_filters(events: list[dict], f: dict) -> list[dict]:
        q = str(f.get("q") or "").strip().lower()
        accion = str(f.get("accion") or "").strip()
        categoria = str(f.get("categoria") or "").strip()
        operacion = str(f.get("operacion") or "").strip()
        severidad = str(f.get("severidad") or "").strip()
        resultado = str(f.get("resultado") or "").strip()
        ip = str(f.get("ip") or "").strip()
        desde = str(f.get("desde") or "").strip()
        hasta = str(f.get("hasta") or "").strip()
        fk_usuario = f.get("fk_usuario")

        def keep(e: dict) -> bool:
            if accion and e["accion"] != accion:
                return False
            if categoria and e["categoria"] != categoria:
                return False
            if operacion and e["operacion"] != operacion:
                return False
            if severidad and e["severidad"] != severidad:
                return False
            if resultado and e["resultado"] != resultado:
                return False
            if ip and ip not in e["direccion_ip"]:
                return False
            if fk_usuario not in (None, "", "todos"):
                try:
                    if e["fk_usuario"] != int(fk_usuario):
                        return False
                except (TypeError, ValueError):
                    pass
            fecha = e["fecha_hora"][:10]
            if desde and fecha and fecha < desde:
                return False
            if hasta and fecha and fecha > hasta:
                return False
            if q:
                haystack = " ".join(
                    [
                        e["usuario"],
                        e["email"],
                        e["accion"],
                        e["accion_label"],
                        e["detalle"],
                        e["tabla_afectada"],
                        e["direccion_ip"],
                        e["rol"],
                    ]
                ).lower()
                if q not in haystack:
                    return False
            return True

        return [e for e in events if keep(e)]

    # ── Estadísticas sobre el conjunto filtrado ──
    @staticmethod
    def _stats(events: list[dict]) -> dict[str, Any]:
        total = len(events)
        fallos = sum(1 for e in events if e["resultado"] == "fallo")
        criticos = sum(1 for e in events if e["severidad"] in ("critico", "alto"))
        usuarios = {e["fk_usuario"] for e in events if e["fk_usuario"] is not None}
        ips = {e["direccion_ip"] for e in events if e["direccion_ip"]}
        por_categoria: dict[str, int] = {}
        for e in events:
            por_categoria[e["categoria"]] = por_categoria.get(e["categoria"], 0) + 1
        return {
            "total": total,
            "fallos_seguridad": fallos,
            "eventos_criticos": criticos,
            "usuarios_distintos": len(usuarios),
            "ips_distintas": len(ips),
            "por_categoria": por_categoria,
        }

    # ── API pública ──
    def query(self, filters: dict, page: int = 1, per_page: int = 15) -> dict[str, Any]:
        all_events = self._load_enriched()
        filtered = self._apply_filters(all_events, filters)
        per_page = max(1, min(100, int(per_page)))
        page = max(1, int(page))
        total = len(filtered)
        total_pages = max(1, math.ceil(total / per_page))
        page = min(page, total_pages)
        start = (page - 1) * per_page
        page_items = filtered[start : start + per_page]

        # Catálogos para los filtros (sobre TODO el dataset, no el filtrado).
        acciones = sorted({(e["accion"], e["accion_label"]) for e in all_events})
        categorias = sorted({e["categoria"] for e in all_events})
        return {
            "items": page_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "stats": self._stats(filtered),
            "acciones": [{"value": a, "label": lbl} for a, lbl in acciones],
            "categorias": categorias,
        }

    def backfill_session_close_targets(self) -> dict[str, int]:
        """
        Completa registros antiguos de SESSION_CLOSED_BY_ADMIN cuyo detalle no
        indica a qué usuario se le cerró la sesión. Asigna un objetivo ficticio
        pero realista (otros usuarios existentes). Idempotente: sólo toca filas
        con el formato antiguo ("…cerró sesión id=").
        """
        try:
            df = self.store.read_table("app_audit_logs")
        except Exception:
            return {"actualizados": 0, "total_admin_close": 0}
        if df.empty or "accion" not in df.columns:
            return {"actualizados": 0, "total_admin_close": 0}

        users = self._users_map()
        # Candidatos como objetivo: usuarios reales (excluye admins).
        candidatos = [
            (uid, info)
            for uid, info in users.items()
            if str(info.get("rol", "")).lower() != "admin"
        ] or list(users.items())
        if not candidatos:
            candidatos = [
                (0, {"nombre": "Carla Méndez", "email": "carla.mendez@fiscalia.gob", "rol": "Detective", "placa": "CPD-2207"}),
                (0, {"nombre": "Luis Paredes", "email": "luis.paredes@fiscalia.gob", "rol": "Oficial", "placa": "CPD-3315"}),
            ]

        actualizados = 0
        total = 0
        for idx in df.index:
            if str(df.at[idx, "accion"]) != "SESSION_CLOSED_BY_ADMIN":
                continue
            total += 1
            detalle = str(df.at[idx, "detalle"] or "")
            # Ya tiene objetivo (formato nuevo "cerró la sesión de ...").
            if "cerró la sesión de" in detalle:
                continue
            try:
                raw_admin = df.at[idx, "fk_usuario"]
                admin_id = int(raw_admin) if raw_admin is not None and not pd.isna(raw_admin) else None
            except (TypeError, ValueError):
                admin_id = None
            admin_info = users.get(admin_id, {}) if admin_id is not None else {}
            admin_label = admin_info.get("nombre") or (f"Administrador #{admin_id}" if admin_id else "Administrador")
            # Elige objetivo determinista según la fila para que no cambie entre corridas.
            target = candidatos[idx % len(candidatos)][1]
            objetivo = target.get("nombre") or target.get("email") or "usuario"
            email = target.get("email") or ""
            rol = target.get("rol") or ""
            nuevo = (
                f"{admin_label} cerró la sesión de {objetivo}"
                + (f" ({email})" if email else "")
                + (f" — rol {rol}" if rol else "")
            )
            df.at[idx, "detalle"] = nuevo
            actualizados += 1

        if actualizados:
            self.store.write_table("app_audit_logs", df)
        return {"actualizados": actualizados, "total_admin_close": total}

    def export_csv(self, filters: dict, limit: int = 5000) -> bytes:
        events = self._apply_filters(self._load_enriched(), filters)[:limit]
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "id_log",
                "fecha_hora_utc",
                "usuario",
                "email",
                "rol",
                "placa",
                "accion",
                "accion_legible",
                "categoria",
                "operacion",
                "severidad",
                "resultado",
                "tabla_afectada",
                "detalle",
                "direccion_ip",
            ]
        )
        for e in events:
            writer.writerow(
                [
                    e["id_log"],
                    e["fecha_hora"],
                    e["usuario"],
                    e["email"],
                    e["rol"],
                    e["placa"],
                    e["accion"],
                    e["accion_label"],
                    e["categoria"],
                    e["operacion"],
                    e["severidad"],
                    e["resultado"],
                    e["tabla_afectada"],
                    e["detalle"],
                    e["direccion_ip"],
                ]
            )
        # BOM para que Excel respete acentos.
        return ("\ufeff" + buf.getvalue()).encode("utf-8")
