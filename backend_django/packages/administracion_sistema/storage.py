"""
Almacenamiento Parquet del paquete Administración del Sistema (MinIO).
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore

ADMIN_COLLECTIONS = [
    "sys_permisos",
    "sys_rol_permisos",
    "sys_politicas_seguridad",
    "sys_parametros",
    "sys_respaldos_config",
    "sys_respaldos_historial",
    "sys_catalogo_delitos",
    "sys_zonas_geograficas",
]

SCHEMAS: dict[str, list[str]] = {
    "sys_permisos": ["id_permiso", "codigo", "nombre", "modulo", "descripcion"],
    "sys_rol_permisos": ["id", "fk_rol", "codigo_permiso"],
    "sys_politicas_seguridad": [
        "id_politica",
        "nombre",
        "clave",
        "valor",
        "activa",
        "descripcion",
    ],
    "sys_parametros": ["id_param", "clave", "valor", "tipo", "descripcion"],
    "sys_respaldos_config": [
        "id",
        "nombre",
        "frecuencia",
        "destino_minio_prefix",
        "tipo_respaldo",
        "hora_programada",
        "activo",
        "ultima_ejecucion",
        "ultimo_estado",
        "proxima_ejecucion",
    ],
    "sys_respaldos_historial": [
        "id",
        "fk_config",
        "nombre_config",
        "tipo_respaldo",
        "frecuencia",
        "destino",
        "iniciado_en",
        "finalizado_en",
        "estado",
        "tablas_copiadas",
        "detalle",
        "es_manual",
        "ejecutado_por",
    ],
    "sys_catalogo_delitos": [
        "id",
        "iucr",
        "primary_type",
        "description",
        "fbi_code",
        "activo",
    ],
    "sys_zonas_geograficas": [
        "id",
        "nombre",
        "tipo_zona",
        "distrito",
        "comunidad",
        "lat_centro",
        "lon_centro",
        "activa",
    ],
}

ID_COL = {
    "sys_permisos": "id_permiso",
    "sys_rol_permisos": "id",
    "sys_politicas_seguridad": "id_politica",
    "sys_parametros": "id_param",
    "sys_respaldos_config": "id",
    "sys_respaldos_historial": "id",
    "sys_catalogo_delitos": "id",
    "sys_zonas_geograficas": "id",
}


class AdminMinioStore(MinioParquetStore):
    def __init__(self) -> None:
        super().__init__()
        self.prefix = os.getenv("MINIO_ADMIN_PREFIX", "datasets/admin")

    def read_table(self, name: str) -> pd.DataFrame:
        if name not in ADMIN_COLLECTIONS:
            raise ValueError(f"Tabla admin desconocida: {name}")
        df = self.read_df(name, use_cache=False)
        if df.empty:
            return pd.DataFrame(columns=SCHEMAS[name])
        return df

    def write_table(self, name: str, df: pd.DataFrame) -> None:
        if name not in ADMIN_COLLECTIONS:
            raise ValueError(f"Tabla admin desconocida: {name}")
        self.write_df(name, df)

    def append_row(self, name: str, row: dict[str, Any]) -> dict[str, Any]:
        df = self.read_table(name)
        id_col = ID_COL[name]
        if id_col not in row or row[id_col] is None:
            row[id_col] = int(df[id_col].max()) + 1 if len(df) else 1
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        self.write_table(name, df)
        return row

    def update_row(self, name: str, row_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
        df = self.read_table(name)
        id_col = ID_COL[name]
        mask = df[id_col] == row_id
        if not mask.any():
            return None
        for k, v in updates.items():
            if k in df.columns and k != id_col:
                df.loc[mask, k] = v
        self.write_table(name, df)
        return df[mask].iloc[0].to_dict()

    def delete_row(self, name: str, row_id: int) -> bool:
        df = self.read_table(name)
        id_col = ID_COL[name]
        before = len(df)
        df = df[df[id_col] != row_id]
        if len(df) == before:
            return False
        self.write_table(name, df)
        return True

    def init_all(self) -> None:
        for name in ADMIN_COLLECTIONS:
            self.write_table(name, pd.DataFrame(columns=SCHEMAS[name]))
