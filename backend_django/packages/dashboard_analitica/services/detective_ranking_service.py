"""
Ranking de detectives desde asignaciones reales (app_asignaciones + app_usuarios).
No usa investigador_asignado ficticio del ETL en dim_caso.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.seed import FK_ROL_DETECTIVE
from packages.shared.minio_transactional import TransactionalMinioStore

ESTADOS_RESUELTOS = frozenset(
    {"cerrado", "resuelto", "closed", "resuelta", "cerrada", "archivado"}
)


def detective_ranking_from_assignments(*, limit: int = 10) -> list[dict[str, Any]]:
    tx = TransactionalMinioStore()
    users = tx.read_table("app_usuarios")
    asig = tx.read_table("app_asignaciones")

    if users.empty or asig.empty:
        return []

    detective_ids = set(
        users.loc[users["fk_rol"].astype(int) == FK_ROL_DETECTIVE, "id_usuario"].astype(int)
    )
    if not detective_ids:
        return []

    labels: dict[int, str] = {}
    for row in users[users["fk_rol"].astype(int) == FK_ROL_DETECTIVE].to_dict(orient="records"):
        uid = int(row["id_usuario"])
        placa = str(row.get("numero_placa") or "").strip()
        apellidos = str(row.get("apellidos") or "").strip()
        nombres = str(row.get("nombres") or "").strip()
        base = f"Det. {apellidos}, {nombres}".strip(", ")
        labels[uid] = f"{base} ({placa})" if placa else base

    active = asig[asig["estado_asignacion"].astype(str) == "Activa"]
    if active.empty:
        return []

    stats: dict[int, dict[str, Any]] = {}
    for row in active.to_dict(orient="records"):
        fk = int(row["fk_detective"])
        if fk not in detective_ids:
            continue
        bucket = stats.setdefault(
            fk,
            {
                "detective": labels.get(fk) or str(row.get("detective_nombre") or f"Detective #{fk}"),
                "casos_asignados": 0,
                "casos_resueltos": 0,
                "fk_detective": fk,
            },
        )
        bucket["casos_asignados"] += 1
        estado = str(row.get("estado_caso_snapshot") or "").lower().strip()
        if estado in ESTADOS_RESUELTOS:
            bucket["casos_resueltos"] += 1

    rows = list(stats.values())
    rows.sort(
        key=lambda x: (-int(x["casos_asignados"]), -int(x["casos_resueltos"]), x["detective"])
    )

    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows[:limit], start=1):
        asignados = int(row["casos_asignados"])
        resueltos = int(row["casos_resueltos"])
        out.append(
            {
                "rank": i,
                "detective": row["detective"],
                "fk_detective": row["fk_detective"],
                "casos_asignados": asignados,
                "casos_resueltos": resueltos,
                "tasa_resolucion": round((resueltos / asignados * 100) if asignados else 0, 1),
            }
        )
    return out


def assignment_resolution_totals() -> dict[str, int]:
    """Totales de resolución desde asignaciones activas (tiempo real)."""
    tx = TransactionalMinioStore()
    asig = tx.read_table("app_asignaciones")
    if asig.empty:
        return {"total_casos": 0, "casos_resueltos": 0}
    active = asig[asig["estado_asignacion"].astype(str) == "Activa"]
    total = int(len(active))
    if total == 0:
        return {"total_casos": 0, "casos_resueltos": 0}
    resueltos = 0
    for row in active.to_dict(orient="records"):
        estado = str(row.get("estado_caso_snapshot") or "").lower().strip()
        if estado in ESTADOS_RESUELTOS:
            resueltos += 1
    return {"total_casos": total, "casos_resueltos": resueltos}


def live_investigation_metrics(*, ranking_limit: int = 15) -> dict[str, Any]:
    ranking = detective_ranking_from_assignments(limit=ranking_limit)
    totals = assignment_resolution_totals()
    total = int(totals["total_casos"])
    resueltos = int(totals["casos_resueltos"])
    return {
        "detective_ranking": ranking,
        "tasa_resolucion": {
            "porcentaje": round((resueltos / total * 100) if total else 0, 2),
            "casos_resueltos": resueltos,
            "total_casos": total,
            "source": "app_asignaciones",
        },
    }
