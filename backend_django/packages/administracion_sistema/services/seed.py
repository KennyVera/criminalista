from __future__ import annotations

from typing import Any

import pandas as pd

from packages.administracion_sistema.storage import SCHEMAS, AdminMinioStore

DEFAULT_PERMISOS = [
    ("dashboard.ver", "Ver dashboard", "dashboard", "Acceso al panel ejecutivo"),
    ("dims.crud", "CRUD dimensiones", "datos", "Gestionar tablas dim_*"),
    ("facts.crud", "CRUD hechos", "datos", "Gestionar fact_crimes"),
    ("raw.ver", "Ver crimes_220k", "datos", "Consultar dataset crudo"),
    ("etl.ejecutar", "Ejecutar ETL", "analitica", "PB a MinIO"),
    ("evidencias.gestionar", "Gestionar evidencias", "evidencias", "Subir y custodiar archivos"),
    ("usuarios.gestionar", "Gestionar usuarios", "admin", "Registrar y editar usuarios"),
    ("permisos.gestionar", "Gestionar permisos", "admin", "Asignar permisos por rol"),
    ("politicas.gestionar", "Políticas de seguridad", "admin", "Configurar políticas"),
    ("sistema.configurar", "Configurar sistema", "admin", "Parámetros y respaldos"),
    ("catalogos.gestionar", "Catálogos de delitos", "admin", "IUCR y tipos"),
    ("zonas.gestionar", "Zonas geográficas", "admin", "Áreas operativas"),
    ("auditoria.ver", "Ver auditoría", "auditoria", "Logs de trazabilidad"),
    (
        "asignaciones.gestionar",
        "Gestionar asignaciones",
        "investigaciones",
        "Asignar, reasignar y remover detectives en casos",
    ),
    (
        "asignaciones.progreso",
        "Consultar progreso investigación",
        "investigaciones",
        "Ver expedientes asignados y avance",
    ),
    ("dashboard.ver", "Ver dashboard analítico", "analitica", "KPIs y gráficas ejecutivas"),
    (
        "dashboard.indicadores",
        "Indicadores operativos",
        "analitica",
        "Tendencias y tasa de resolución",
    ),
]

DEFAULT_POLITICAS = [
    ("Longitud mínima contraseña", "pwd_min_length", "8", True),
    ("Intentos login máximos", "login_max_attempts", "5", True),
    ("Sesión expira (horas)", "session_hours", "12", True),
    ("2FA obligatorio Admin", "admin_2fa_required", "true", True),
]

DEFAULT_PARAMETROS = [
    ("app_nombre", "CrimeTrack Analytics Corp", "string", "Nombre del aplicativo"),
    ("registros_por_pagina", "25", "int", "Registros por páginas"),
    ("timezone", "America/Bogota", "string", "Zona horaria"),
    (
        "app_subtitulo",
        "Panel de analítica criminal — ISO 9241-210",
        "string",
        "Subtítulo del aplicativo",
    ),
    ("app_icon_url", "", "string", "Logo del aplicativo (URL o base64)"),
    (
        "combobox_opciones_visibles",
        "10",
        "int",
        "Opciones visibles en listas desplegables antes del scroll",
    ),
]

DEFAULT_RESPALDO = [
    (
        "Respaldo diario MinIO",
        "diario",
        "backups/daily",
        "completo",
        "02:00",
        True,
        "",
        "Pendiente de primera ejecución",
        "",
    ),
]

DEFAULT_CATALOGOS = [
    ("06", "THEFT", "Theft over $500", "theft", True),
    ("08A", "BATTERY", "Simple battery", "assault", True),
    ("05", "BURGLARY", "Unlawful entry", "burglary", True),
]

DEFAULT_ZONAS = [
    ("Zona Norte CPD", "Operativa", "01", "20", "41.90", "-87.65", True),
    ("Zona Sur CPD", "Operativa", "07", "35", "41.75", "-87.62", True),
]


def seed_admin_tables(*, reset: bool = False) -> dict[str, Any]:
    store = AdminMinioStore()
    if reset:
        store.init_all()

    permisos = pd.DataFrame(
        [
            {
                "id_permiso": i + 1,
                "codigo": c,
                "nombre": n,
                "modulo": m,
                "descripcion": d,
            }
            for i, (c, n, m, d) in enumerate(DEFAULT_PERMISOS)
        ]
    )
    store.write_table("sys_permisos", permisos)

    # Admin (1) todos los permisos; otros roles subset
    rol_perms = []
    rid = 1
    all_codes = [p[0] for p in DEFAULT_PERMISOS]
    for fk_rol, codes in [
        (1, all_codes),
        (
            2,
            [
                "dashboard.ver",
                "asignaciones.gestionar",
                "asignaciones.progreso",
            ],
        ),
        (
            3,
            [
                "dashboard.ver",
                "facts.crud",
                "raw.ver",
                "evidencias.gestionar",
                "asignaciones.progreso",
            ],
        ),
        (4, ["dashboard.ver", "raw.ver"]),
        (
            5,
            [
                "dashboard.ver",
                "dashboard.indicadores",
                "dims.crud",
                "facts.crud",
                "raw.ver",
                "etl.ejecutar",
            ],
        ),
    ]:
        for code in codes:
            rol_perms.append({"id": rid, "fk_rol": fk_rol, "codigo_permiso": code})
            rid += 1
    store.write_table("sys_rol_permisos", pd.DataFrame(rol_perms))

    politicas = pd.DataFrame(
        [
            {
                "id_politica": i + 1,
                "nombre": n,
                "clave": k,
                "valor": v,
                "activa": a,
                "descripcion": "",
            }
            for i, (n, k, v, a) in enumerate(DEFAULT_POLITICAS)
        ]
    )
    store.write_table("sys_politicas_seguridad", politicas)

    params = pd.DataFrame(
        [
            {
                "id_param": i + 1,
                "clave": k,
                "valor": v,
                "tipo": t,
                "descripcion": d,
            }
            for i, (k, v, t, d) in enumerate(DEFAULT_PARAMETROS)
        ]
    )
    store.write_table("sys_parametros", params)

    respaldos = pd.DataFrame(
        [
            {
                "id": 1,
                "nombre": n,
                "frecuencia": f,
                "destino_minio_prefix": p,
                "tipo_respaldo": t,
                "hora_programada": h,
                "activo": a,
                "ultima_ejecucion": u,
                "ultimo_estado": e,
                "proxima_ejecucion": px,
            }
            for (n, f, p, t, h, a, u, e, px) in DEFAULT_RESPALDO
        ]
    )
    store.write_table("sys_respaldos_config", respaldos)
    store.write_table(
        "sys_respaldos_historial",
        pd.DataFrame(columns=SCHEMAS["sys_respaldos_historial"]),
    )

    catalogos = pd.DataFrame(
        [
            {
                "id": i + 1,
                "iucr": iucr,
                "primary_type": pt,
                "description": desc,
                "fbi_code": fbi,
                "activo": act,
            }
            for i, (iucr, pt, desc, fbi, act) in enumerate(DEFAULT_CATALOGOS)
        ]
    )
    store.write_table("sys_catalogo_delitos", catalogos)

    zonas = pd.DataFrame(
        [
            {
                "id": i + 1,
                "nombre": n,
                "tipo_zona": tz,
                "distrito": d,
                "comunidad": c,
                "lat_centro": lat,
                "lon_centro": lon,
                "activa": act,
            }
            for i, (n, tz, d, c, lat, lon, act) in enumerate(DEFAULT_ZONAS)
        ]
    )
    store.write_table("sys_zonas_geograficas", zonas)

    return {"tables": ADMIN_COLLECTIONS, "permisos": len(permisos), "rol_permisos": len(rol_perms)}
