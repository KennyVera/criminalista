"""Lectura de políticas de seguridad (sys_politicas_seguridad en MinIO)."""

from __future__ import annotations

from packages.administracion_sistema.storage import AdminMinioStore

DEFAULT_LOGIN_MAX_ATTEMPTS = 5


def _is_active(value) -> bool:
    return str(value).lower() in ("true", "1", "yes", "si", "sí", "t")


def get_login_max_attempts() -> int:
    """Intentos fallidos permitidos antes de bloquear la cuenta."""
    try:
        df = AdminMinioStore().read_table("sys_politicas_seguridad")
    except Exception:
        return DEFAULT_LOGIN_MAX_ATTEMPTS
    if df.empty or "clave" not in df.columns:
        return DEFAULT_LOGIN_MAX_ATTEMPTS

    rows = df[df["clave"].astype(str) == "login_max_attempts"]
    if rows.empty:
        return DEFAULT_LOGIN_MAX_ATTEMPTS

    row = rows.iloc[0]
    if "activa" in row.index and not _is_active(row["activa"]):
        return DEFAULT_LOGIN_MAX_ATTEMPTS

    try:
        n = int(str(row["valor"]).strip())
        return max(1, min(n, 50))
    except (TypeError, ValueError):
        return DEFAULT_LOGIN_MAX_ATTEMPTS
