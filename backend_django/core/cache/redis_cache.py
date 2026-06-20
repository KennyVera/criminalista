"""
Decoradores de caché Redis con generación versionada (invalidación por evento ETL).
"""

from __future__ import annotations

import hashlib
import json
from functools import wraps
from typing import Any, Callable

from django.core.cache import cache

CACHE_GENERATION_KEY = "crimetrack:cache:generation"
DEFAULT_EXPEDIENTE_TTL = 300
DEFAULT_ADMIN_TTL = 600


def get_cache_generation() -> int:
    gen = cache.get(CACHE_GENERATION_KEY)
    if gen is None:
        cache.set(CACHE_GENERATION_KEY, 1, None)
        return 1
    return int(gen)


def _stable_key(prefix: str, *parts: Any) -> str:
    gen = get_cache_generation()
    raw = ":".join(str(p) for p in parts if p is not None and str(p) != "")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"crimetrack:g{gen}:{prefix}:{digest}"


def cache_response(
    prefix: str,
    *,
    ttl: int = DEFAULT_EXPEDIENTE_TTL,
    key_builder: Callable[..., str] | None = None,
) -> Callable:
    """
    Cachea respuestas JSON-serializables de vistas DRF.
    key_builder(recv, *args, **kwargs) -> str identificador estable.
    """

    def decorator(view_method: Callable) -> Callable:
        @wraps(view_method)
        def wrapper(self, request, *args, **kwargs):
            if request.method not in ("GET", "HEAD"):
                return view_method(self, request, *args, **kwargs)

            if key_builder is not None:
                ident = key_builder(request, *args, **kwargs)
            else:
                ident = request.get_full_path()

            user = getattr(request, "crimetrack_user", None) or {}
            role = str(user.get("nombre_rol", "anon"))
            uid = user.get("id_usuario", "0")
            cache_key = _stable_key(prefix, role, uid, ident)

            cached = cache.get(cache_key)
            if cached is not None:
                if isinstance(cached, dict):
                    cached = {**cached, "_from_cache": True}
                return _clone_response(cached)

            response = view_method(self, request, *args, **kwargs)
            payload = _extract_payload(response)
            if payload is not None:
                cache.set(cache_key, payload, ttl)
            return response

        return wrapper

    return decorator


def _extract_payload(response: Any) -> Any | None:
    data = getattr(response, "data", None)
    if data is None:
        return None
    try:
        json.dumps(data, default=str)
        return data
    except (TypeError, ValueError):
        return None


def _clone_response(payload: Any) -> Any:
    from rest_framework.response import Response

    return Response(payload)
