"""
Tablas transaccionales en MinIO (Parquet) — capa operativa RBAC, evidencias, auditoría.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore

TRANSACTIONAL_COLLECTIONS = [
    "app_roles",
    "app_usuarios",
    "app_sesiones_activas",
    "app_involucrados",
    "app_caso_involucrado",
    "app_evidencias",
    "app_asignaciones",
    "app_casos_operativos",
    "app_expediente_bitacora",
    "app_audit_logs",
    "app_dashboard_summary",
    "app_patrullas",
    "app_patrulla_oficiales",
    "app_incidentes",
]

SCHEMAS: dict[str, list[str]] = {
    "app_roles": ["id_rol", "nombre_rol", "descripcion"],
    "app_usuarios": [
        "id_usuario",
        "fk_rol",
        "numero_placa",
        "nombres",
        "apellidos",
        "email",
        "password_hash",
        "estado_cuenta",
        "intentos_login_fallidos",
        "fecha_creacion",
    ],
    "app_sesiones_activas": [
        "id_sesion",
        "fk_usuario",
        "token_jti",
        "email",
        "nombre_rol",
        "numero_placa",
        "nombres",
        "apellidos",
        "direccion_ip",
        "user_agent",
        "fecha_inicio",
        "fecha_ultimo_acceso",
        "fecha_expiracion",
        "activa",
        "fecha_cierre",
        "motivo_cierre",
    ],
    "app_involucrados": [
        "id_involucrado",
        "identificacion",
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "antecedentes",
    ],
    "app_caso_involucrado": [
        "id_relacion",
        "fk_caso",
        "fk_involucrado",
        "tipo_relacion",
        "declaracion",
        "fecha_asociacion",
    ],
    "app_evidencias": [
        "id_evidencia",
        "fk_caso",
        "fk_usuario_carga",
        "tipo_evidencia",
        "nombre_archivo",
        "minio_url",
        "peso_mb",
        "hash_sha256",
        "algoritmo_hash",
        "estado_custodia",
        "fecha_subida",
        "fecha_actualizacion_custodia",
        "fk_usuario_custodia",
    ],
    "app_asignaciones": [
        "id_asignacion",
        "fk_caso",
        "case_number",
        "fk_detective",
        "detective_nombre",
        "detective_placa",
        "fk_comisario",
        "comisario_nombre",
        "fecha_asignacion",
        "estado_asignacion",
        "notificado",
        "fecha_notificacion",
        "observaciones",
        "fecha_cierre",
        "motivo_cierre",
        "estado_caso_snapshot",
        "prioridad_caso_snapshot",
        "fecha_reporte_snapshot",
        "observaciones_caso_snapshot",
        "avance_pct_actual",
    ],
    "app_casos_operativos": [
        "id",
        "case_number",
        "estado_caso",
        "fecha_reporte",
        "prioridad_caso",
        "investigador_asignado",
        "indexado_en",
    ],
    "app_expediente_bitacora": [
        "id_bitacora",
        "case_number",
        "fk_caso",
        "fk_usuario",
        "autor_nombre",
        "nota",
        "avance_pct",
        "estado_caso",
        "fecha_hora",
    ],
    "app_audit_logs": [
        "id_log",
        "fk_usuario",
        "accion",
        "tabla_afectada",
        "detalle",
        "datos_anteriores",
        "datos_nuevos",
        "direccion_ip",
        "fecha_hora",
        "previous_hash",
        "event_hash",
    ],
    "app_patrullas": [
        "id_patrulla",
        "codigo",
        "sector",
        "turno",
        "estado",
        "fk_comisario",
        "comisario_nombre",
        "notas",
        "fecha_creacion",
        "fecha_actualizacion",
        "activo",
    ],
    "app_patrulla_oficiales": [
        "id_patrulla_oficial",
        "fk_patrulla",
        "fk_oficial",
        "oficial_nombre",
        "oficial_placa",
        "rol_patrulla",
        "fecha_asignacion",
        "estado",
    ],
    "app_incidentes": [
        "id_incidente",
        "codigo",
        "tipo",
        "descripcion",
        "ubicacion",
        "prioridad",
        "estado",
        "reportante",
        "fk_patrulla",
        "patrulla_codigo",
        "fk_operador",
        "operador_nombre",
        "fk_comisario",
        "comisario_nombre",
        "notas_despacho",
        "apoyo_solicitado",
        "resultado_atencion",
        "parte_policial",
        "motivo_devolucion",
        "fecha_reporte",
        "fecha_despacho",
        "fecha_atendido",
        "fecha_cierre",
    ],
    "app_dashboard_summary": [
        "id_summary",
        "clave",
        "payload_json",
        "actualizado_en",
        "filas_hechos",
        "duracion_ms",
    ],
}


class TransactionalMinioStore(MinioParquetStore):
    """Parquet bajo datasets/transactional/."""

    def __init__(self) -> None:
        super().__init__()
        self.prefix = os.getenv("MINIO_TRANSACTIONAL_PREFIX", "datasets/transactional")

    def read_table(self, name: str) -> pd.DataFrame:
        if name not in TRANSACTIONAL_COLLECTIONS:
            raise ValueError(f"Tabla transaccional desconocida: {name}")
        df = self.read_df(name, use_cache=False)
        if df.empty:
            return pd.DataFrame(columns=SCHEMAS[name])
        return df

    def write_table(self, name: str, df: pd.DataFrame) -> None:
        if name not in TRANSACTIONAL_COLLECTIONS:
            raise ValueError(f"Tabla transaccional desconocida: {name}")
        self.write_df(name, df)

    @staticmethod
    def compute_audit_hash(previous_hash: str, row: dict[str, Any]) -> str:
        """Hash encadenado (CU-O75): sella el evento con el hash del anterior."""
        canonical = "|".join(
            str(row.get(field, ""))
            for field in (
                "fk_usuario",
                "accion",
                "tabla_afectada",
                "detalle",
                "datos_anteriores",
                "datos_nuevos",
                "direccion_ip",
                "fecha_hora",
            )
        )
        payload = f"{previous_hash}|{canonical}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def append_row(self, name: str, row: dict[str, Any]) -> dict[str, Any]:
        df = self.read_table(name)
        new_id_col = {
            "app_roles": "id_rol",
            "app_usuarios": "id_usuario",
            "app_sesiones_activas": "id_sesion",
            "app_involucrados": "id_involucrado",
            "app_caso_involucrado": "id_relacion",
            "app_evidencias": "id_evidencia",
            "app_asignaciones": "id_asignacion",
            "app_casos_operativos": "id",
            "app_expediente_bitacora": "id_bitacora",
            "app_audit_logs": "id_log",
            "app_dashboard_summary": "id_summary",
            "app_patrullas": "id_patrulla",
            "app_patrulla_oficiales": "id_patrulla_oficial",
            "app_incidentes": "id_incidente",
        }[name]
        if new_id_col not in row or row[new_id_col] is None:
            row[new_id_col] = int(df[new_id_col].max()) + 1 if len(df) else 1
        if name == "app_audit_logs":
            # Sello criptográfico encadenado: cada evento incluye el hash del previo.
            prev_hash = ""
            if len(df) and "event_hash" in df.columns:
                ordered = df.sort_values("id_log")
                last = str(ordered["event_hash"].iloc[-1] or "")
                prev_hash = last
            row["previous_hash"] = prev_hash
            row["event_hash"] = self.compute_audit_hash(prev_hash, row)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        self.write_table(name, df)
        return row

    def init_empty_tables(self) -> dict[str, int]:
        summary = {}
        for name in TRANSACTIONAL_COLLECTIONS:
            self.write_table(name, pd.DataFrame(columns=SCHEMAS[name]))
            summary[name] = 0
        return summary

    def ensure_tables(self) -> None:
        for name in TRANSACTIONAL_COLLECTIONS:
            try:
                self.read_table(name)
            except Exception:
                self.write_table(name, pd.DataFrame(columns=SCHEMAS[name]))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
