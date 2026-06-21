from __future__ import annotations

from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.passwords import hash_password
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

# Credenciales por defecto (desarrollo)
DEFAULT_ADMIN_EMAIL = "kennyvera43@gmail.com"
DEFAULT_ADMIN_PASSWORD = "CrimeTrack2026!"
DEFAULT_ADMIN_PLACA = "CPD-1001"

DEFAULT_COMISARIO_EMAIL = "comisario@crimetrack.local"
DEFAULT_COMISARIO_PASSWORD = "Comisario2026!"
DEFAULT_COMISARIO_PLACA = "CPD-2001"

DEFAULT_DETECTIVE_EMAIL = "detective@crimetrack.local"
DEFAULT_DETECTIVE_PASSWORD = "Detective2026!"
DEFAULT_DETECTIVE_PLACA = "CPD-3001"

FK_ROL_COMISARIO = 2
FK_ROL_DETECTIVE = 3


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
            },
            {
                "id_usuario": 2,
                "fk_rol": FK_ROL_COMISARIO,
                "numero_placa": DEFAULT_COMISARIO_PLACA,
                "nombres": "María",
                "apellidos": "López",
                "email": DEFAULT_COMISARIO_EMAIL,
                "password_hash": hash_password(DEFAULT_COMISARIO_PASSWORD),
                "estado_cuenta": "Activa",
                "intentos_login_fallidos": 0,
                "fecha_creacion": utc_now_iso(),
            },
            {
                "id_usuario": 3,
                "fk_rol": FK_ROL_DETECTIVE,
                "numero_placa": DEFAULT_DETECTIVE_PLACA,
                "nombres": "Carlos",
                "apellidos": "Ramírez",
                "email": DEFAULT_DETECTIVE_EMAIL,
                "password_hash": hash_password(DEFAULT_DETECTIVE_PASSWORD),
                "estado_cuenta": "Activa",
                "intentos_login_fallidos": 0,
                "fecha_creacion": utc_now_iso(),
            },
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
        "credentials": _default_credentials_payload(),
        "minio_prefix": store.prefix,
        "tables": [
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
        ],
    }


def _default_credentials_payload() -> list[dict[str, str]]:
    return [
        {
            "rol": "Admin",
            "email": DEFAULT_ADMIN_EMAIL,
            "password": DEFAULT_ADMIN_PASSWORD,
            "numero_placa": DEFAULT_ADMIN_PLACA,
        },
        {
            "rol": "Comisario",
            "email": DEFAULT_COMISARIO_EMAIL,
            "password": DEFAULT_COMISARIO_PASSWORD,
            "numero_placa": DEFAULT_COMISARIO_PLACA,
        },
        {
            "rol": "Detective",
            "email": DEFAULT_DETECTIVE_EMAIL,
            "password": DEFAULT_DETECTIVE_PASSWORD,
            "numero_placa": DEFAULT_DETECTIVE_PLACA,
        },
    ]


def ensure_operational_users(
    store: TransactionalMinioStore | None = None,
) -> dict[str, Any]:
    """
    Añade Comisario y Detective si no existen (no borra usuarios actuales).
    Garantiza roles en app_roles.
    """
    store = store or TransactionalMinioStore()
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

    df = store.read_table("app_usuarios")
    if df.empty:
        df = pd.DataFrame(columns=store.read_table("app_usuarios").columns)

    emails = set(df["email"].astype(str).str.lower()) if not df.empty else set()
    next_id = int(df["id_usuario"].max()) + 1 if not df.empty and "id_usuario" in df.columns else 1

    to_add = [
        (
            DEFAULT_COMISARIO_EMAIL,
            FK_ROL_COMISARIO,
            DEFAULT_COMISARIO_PLACA,
            "María",
            "López",
            DEFAULT_COMISARIO_PASSWORD,
        ),
        (
            DEFAULT_DETECTIVE_EMAIL,
            FK_ROL_DETECTIVE,
            DEFAULT_DETECTIVE_PLACA,
            "Carlos",
            "Ramírez",
            DEFAULT_DETECTIVE_PASSWORD,
        ),
        ("oficial1@crimetrack.local", 4, "OF-4001", "Jorge", "Mendoza", "Oficial2026!"),
        ("oficial2@crimetrack.local", 4, "OF-4002", "Lucía", "Torres", "Oficial2026!"),
        ("oficial3@crimetrack.local", 4, "OF-4003", "Andrés", "Vega", "Oficial2026!"),
    ]

    created: list[str] = []
    skipped: list[str] = []
    for email, fk_rol, placa, nombres, apellidos, password in to_add:
        key = email.lower()
        if key in emails:
            skipped.append(email)
            continue
        row = {
            "id_usuario": next_id,
            "fk_rol": fk_rol,
            "numero_placa": placa,
            "nombres": nombres,
            "apellidos": apellidos,
            "email": key,
            "password_hash": hash_password(password),
            "estado_cuenta": "Activa",
            "intentos_login_fallidos": 0,
            "fecha_creacion": utc_now_iso(),
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        emails.add(key)
        created.append(email)
        next_id += 1

    if created:
        store.write_table("app_usuarios", df)

    return {
        "created": created,
        "skipped": skipped,
        "credentials": _default_credentials_payload(),
    }
