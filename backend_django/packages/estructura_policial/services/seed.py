"""Semilla de estructura policial (Chicago Police Department demo)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso


def seed_estructura_policial(
    store: TransactionalMinioStore | None = None,
    *,
    reset: bool = False,
) -> dict[str, Any]:
    tx = store or TransactionalMinioStore()
    tx.ensure_tables()

    if reset:
        for table in (
            "app_personal_policial",
            "app_estaciones_policiales",
            "app_distritos_policiales",
            "app_departamentos_policiales",
            "app_rangos_policiales",
        ):
            tx.write_table(table, pd.DataFrame(columns=tx.read_table(table).columns))

    rangos = pd.DataFrame(
        [
            {"id_rango": 1, "codigo": "OF", "nombre": "Oficial", "nivel_jerarquico": 1, "descripcion": "Oficial de patrulla", "activo": True},
            {"id_rango": 2, "codigo": "DET", "nombre": "Detective", "nivel_jerarquico": 2, "descripcion": "Investigador criminal", "activo": True},
            {"id_rango": 3, "codigo": "SGT", "nombre": "Sargento", "nivel_jerarquico": 3, "descripcion": "Supervisión de turno", "activo": True},
            {"id_rango": 4, "codigo": "COM", "nombre": "Comisario", "nivel_jerarquico": 4, "descripcion": "Mando de distrito", "activo": True},
            {"id_rango": 5, "codigo": "ADM", "nombre": "Administrador", "nivel_jerarquico": 5, "descripcion": "Administración del sistema", "activo": True},
        ]
    )
    tx.write_table("app_rangos_policiales", rangos)

    deptos = pd.DataFrame(
        [
            {
                "id_departamento": 1,
                "codigo": "CPD",
                "nombre": "Chicago Police Department",
                "ciudad": "Chicago",
                "estado_region": "Illinois",
                "pais": "USA",
                "activo": True,
                "fecha_creacion": utc_now_iso(),
            }
        ]
    )
    tx.write_table("app_departamentos_policiales", deptos)

    distritos = pd.DataFrame(
        [
            {"id_distrito": i, "fk_departamento": 1, "codigo": str(i), "nombre": f"Distrito {i}", "descripcion": f"Distrito policial {i} — CPD", "activo": True}
            for i in range(1, 8)
        ]
    )
    tx.write_table("app_distritos_policiales", distritos)

    estaciones = pd.DataFrame(
        [
            {"id_estacion": 1, "fk_distrito": 1, "codigo": "D1-HQ", "nombre": "1st District HQ", "direccion": "1718 S State St", "telefono": "+1-312-745-4290", "activo": True},
            {"id_estacion": 2, "fk_distrito": 2, "codigo": "D2-HQ", "nombre": "2nd District HQ", "direccion": "5101 S Wentworth Ave", "telefono": "+1-312-745-8366", "activo": True},
            {"id_estacion": 3, "fk_distrito": 3, "codigo": "D3-HQ", "nombre": "3rd District HQ", "direccion": "7040 S Cottage Grove Ave", "telefono": "+1-312-747-9900", "activo": True},
        ]
    )
    tx.write_table("app_estaciones_policiales", estaciones)

    usuarios = tx.read_table("app_usuarios")
    personal_rows = []
    mapping = [
        (1, 5, 1, 1, "CPD-1001", "Kenny", "Vera", "kennyvera43@gmail.com"),
        (2, 4, 1, 1, "CPD-2001", "María", "López", "comisario@crimetrack.local"),
        (3, 2, 2, 2, "CPD-3001", "Carlos", "Ramírez", "detective@crimetrack.local"),
    ]
    now = utc_now_iso()
    pid = 1
    for fk_user, fk_rango, fk_est, fk_dist, placa, nom, ape, email in mapping:
        if not usuarios.empty and fk_user not in set(pd.to_numeric(usuarios["id_usuario"], errors="coerce")):
            continue
        personal_rows.append(
            {
                "id_personal": pid,
                "fk_usuario": fk_user,
                "fk_rango": fk_rango,
                "fk_estacion": fk_est,
                "fk_distrito": fk_dist,
                "fk_departamento": 1,
                "numero_placa": placa,
                "nombres": nom,
                "apellidos": ape,
                "identificacion": "",
                "email_laboral": email,
                "telefono": "",
                "fecha_ingreso": "2020-01-15",
                "estado_laboral": "Activo",
                "activo": True,
                "fecha_creacion": now,
                "fecha_actualizacion": now,
            }
        )
        pid += 1

    if personal_rows:
        tx.write_table("app_personal_policial", pd.DataFrame(personal_rows))

    return {
        "rangos": len(rangos),
        "departamentos": len(deptos),
        "distritos": len(distritos),
        "estaciones": len(estaciones),
        "personal": len(personal_rows),
    }
