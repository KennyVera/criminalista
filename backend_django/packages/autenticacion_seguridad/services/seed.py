from __future__ import annotations

from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.passwords import hash_password
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

# Credenciales por defecto (desarrollo)
DEFAULT_ADMIN_EMAIL = "kennyvera43@gmail.com"
DEFAULT_ADMIN_PASSWORD = "CrimeTrack2026!"
DEFAULT_ADMIN_PLACA = "CPD-1001"


def seed_auth_data(
    store: TransactionalMinioStore | None = None,
    *,
    reset: bool = True,
) -> dict[str, Any]:
    """
    Crea tablas transaccionales en MinIO y usuario administrador inicial.
    """
    store = store or TransactionalMinioStore()
    if reset:
        store.init_empty_tables()
    else:
        store.ensure_tables()

    roles = pd.DataFrame(
        [
            {"id_rol": 1, "nombre_rol": "Admin", "descripcion": "Administrador del sistema"},
            {"id_rol": 2, "nombre_rol": "Comisario", "descripcion": "Mando policial"},
            {"id_rol": 3, "nombre_rol": "Detective", "descripcion": "Investigador"},
            {"id_rol": 4, "nombre_rol": "Oficial", "descripcion": "Oficial operativo"},
            {
                "id_rol": 5,
                "nombre_rol": "Analista Criminal",
                "descripcion": "Analítica criminal y KPIs operativos",
            },
        ]
    )
    store.write_table("app_roles", roles)

    usuarios = pd.DataFrame(
        [
            {
                "id_usuario": 1,
                "fk_rol": 1,
                "numero_placa": DEFAULT_ADMIN_PLACA,
                "nombres": "Kenny",
                "apellidos": "Vera",
                "email": DEFAULT_ADMIN_EMAIL,
                "password_hash": hash_password(DEFAULT_ADMIN_PASSWORD),
                "estado_cuenta": "Activa",
                "intentos_login_fallidos": 0,
                "fecha_creacion": utc_now_iso(),
            }
        ]
    )
    store.write_table("app_usuarios", usuarios)

    store.append_row(
        "app_audit_logs",
        {
            "fk_usuario": 1,
            "accion": "SEED_AUTH",
            "tabla_afectada": "app_usuarios",
            "detalle": "Semilla RBAC y tablas transaccionales en MinIO",
            "direccion_ip": "127.0.0.1",
            "fecha_hora": utc_now_iso(),
        },
    )

    return {
        "roles": len(roles),
        "usuarios": len(usuarios),
        "email": DEFAULT_ADMIN_EMAIL,
        "password": DEFAULT_ADMIN_PASSWORD,
        "numero_placa": DEFAULT_ADMIN_PLACA,
        "minio_prefix": store.prefix,
        "tables": [
            "app_roles",
            "app_usuarios",
            "app_sesiones_activas",
            "app_involucrados",
            "app_caso_involucrado",
            "app_evidencias",
            "app_audit_logs",
        ],
    }
