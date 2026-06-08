from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from django.conf import settings


def _secret() -> str:
    return os.getenv("JWT_SECRET_KEY", settings.SECRET_KEY)


def _exp_hours() -> int:
    env = os.getenv("JWT_EXPIRE_HOURS", "").strip()
    if env:
        try:
            return max(1, min(int(env), 168))
        except ValueError:
            pass
    from packages.autenticacion_seguridad.services.security_policy import (
        get_session_hours,
    )

    return get_session_hours()


def token_expiration() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=_exp_hours())


def create_access_token(payload: dict[str, Any]) -> str:
    exp = token_expiration()
    data = {
        **payload,
        "exp": exp,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(data, _secret(), algorithm="HS256")


def expiration_iso() -> str:
    return token_expiration().isoformat()


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _secret(), algorithms=["HS256"])
