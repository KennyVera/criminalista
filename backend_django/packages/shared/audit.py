"""
Helper centralizado de auditoría (P03 — Auditoría y Trazabilidad).

Punto único de escritura sobre ``app_audit_logs``. Es deliberadamente tolerante a
fallos: la auditoría NUNCA debe romper la operación principal (RNF-O-07). Mantiene
el esquema existente (id_log, fk_usuario, accion, tabla_afectada, detalle,
direccion_ip, fecha_hora) para no romper lo ya implementado.
"""

from __future__ import annotations

import json
from typing import Any

from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

_MAX_JSON_LEN = 6000


def _to_json(value: Any) -> str:
    """Serializa un dict/lista a JSON legible (o cadena vacía). Tolerante a fallos."""
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value[:_MAX_JSON_LEN]
    try:
        text = json.dumps(value, ensure_ascii=False, default=str, indent=2)
        return text[:_MAX_JSON_LEN]
    except Exception:
        return str(value)[:_MAX_JSON_LEN]


def client_ip(request) -> str:
    """IP del cliente respetando proxy (X-Forwarded-For)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or ""


def record_audit(
    *,
    fk_usuario: int | None,
    accion: str,
    detalle: str = "",
    ip: str = "",
    tabla: str = "",
    antes: Any = None,
    despues: Any = None,
) -> None:
    """Registra un evento de auditoría. Silencioso ante errores."""
    try:
        TransactionalMinioStore().append_row(
            "app_audit_logs",
            {
                "fk_usuario": fk_usuario,
                "accion": str(accion),
                "tabla_afectada": tabla or "",
                "detalle": detalle or "",
                "datos_anteriores": _to_json(antes),
                "datos_nuevos": _to_json(despues),
                "direccion_ip": ip or "",
                "fecha_hora": utc_now_iso(),
            },
        )
    except Exception:
        # La auditoría no debe interrumpir la operación de negocio.
        pass


def audit_request(
    request,
    *,
    accion: str,
    detalle: str = "",
    tabla: str = "",
    antes: Any = None,
    despues: Any = None,
) -> None:
    """Registra un evento tomando usuario e IP desde el request autenticado (JWT)."""
    user: dict[str, Any] = getattr(request, "crimetrack_user", {}) or {}
    raw_id = user.get("id_usuario")
    try:
        fk = int(raw_id) if raw_id is not None else None
    except (TypeError, ValueError):
        fk = None
    record_audit(
        fk_usuario=fk,
        accion=accion,
        detalle=detalle,
        ip=client_ip(request),
        tabla=tabla,
        antes=antes,
        despues=despues,
    )
