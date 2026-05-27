"""
Tablas transaccionales en MinIO (Parquet) — capa operativa RBAC, evidencias, auditoría.
"""

from __future__ import annotations

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
    "app_audit_logs",
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
        "minio_url",
        "peso_mb",
        "estado_custodia",
        "fecha_subida",
    ],
    "app_audit_logs": [
        "id_log",
        "fk_usuario",
        "accion",
        "tabla_afectada",
        "detalle",
        "direccion_ip",
        "fecha_hora",
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

    def append_row(self, name: str, row: dict[str, Any]) -> dict[str, Any]:
        df = self.read_table(name)
        new_id_col = {
            "app_roles": "id_rol",
            "app_usuarios": "id_usuario",
            "app_sesiones_activas": "id_sesion",
            "app_involucrados": "id_involucrado",
            "app_caso_involucrado": "id_relacion",
            "app_evidencias": "id_evidencia",
            "app_audit_logs": "id_log",
        }[name]
        if new_id_col not in row or row[new_id_col] is None:
            row[new_id_col] = int(df[new_id_col].max()) + 1 if len(df) else 1
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
