"""Lectura de políticas de seguridad (sys_politicas_seguridad en MinIO)."""

from __future__ import annotations

from packages.administracion_sistema.storage import AdminMinioStore

DEFAULT_LOGIN_MAX_ATTEMPTS = 5
DEFAULT_PWD_MIN_LENGTH = 8
DEFAULT_SESSION_HOURS = 12


def _is_active(value) -> bool:
    return str(value).lower() in ("true", "1", "yes", "si", "sí", "t")


def _get_policy_row(clave: str) -> dict | None:
    try:
        df = AdminMinioStore().read_table("sys_politicas_seguridad")
    except Exception:
        return None
    if df.empty or "clave" not in df.columns:
        return None
    rows = df[df["clave"].astype(str) == clave]
    if rows.empty:
        return None
    row = rows.iloc[0]
    if "activa" in row.index and not _is_active(row["activa"]):
        return None
    return row.to_dict()


def _policy_int(clave: str, default: int, *, min_v: int, max_v: int) -> int:
    row = _get_policy_row(clave)
    if not row:
        return default
    try:
        n = int(str(row.get("valor", default)).strip())
        return max(min_v, min(n, max_v))
    except (TypeError, ValueError):
        return default


def get_login_max_attempts() -> int:
    return _policy_int(
        "login_max_attempts", DEFAULT_LOGIN_MAX_ATTEMPTS, min_v=1, max_v=50
    )


def get_pwd_min_length() -> int:
    return _policy_int("pwd_min_length", DEFAULT_PWD_MIN_LENGTH, min_v=6, max_v=32)


def get_session_hours() -> int:
    return _policy_int("session_hours", DEFAULT_SESSION_HOURS, min_v=1, max_v=168)


def validate_password_strength(password: str) -> None:
    min_len = get_pwd_min_length()
    if len(password) < min_len:
        raise ValueError(
            f"La contraseña debe tener al menos {min_len} caracteres "
            f"(política pwd_min_length)."
        )


def validate_politica_value(clave: str, valor: str) -> str:
    """Normaliza y valida el valor según la clave de política."""
    clave = str(clave).strip()
    raw = str(valor).strip()

    if clave == "pwd_min_length":
        n = int(raw)
        if n < 6 or n > 32:
            raise ValueError("Longitud mínima: entre 6 y 32")
        return str(n)
    if clave == "login_max_attempts":
        n = int(raw)
        if n < 1 or n > 50:
            raise ValueError("Intentos máximos: entre 1 y 50")
        return str(n)
    if clave == "session_hours":
        n = int(raw)
        if n < 1 or n > 168:
            raise ValueError("Horas de sesión: entre 1 y 168")
        return str(n)
    if clave == "admin_2fa_required":
        low = raw.lower()
        if low not in ("true", "false"):
            raise ValueError("Use true o false")
        return low
    return raw
