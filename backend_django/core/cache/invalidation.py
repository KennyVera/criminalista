"""
Invalidación de caché por eventos (ETL Celery, asignaciones, bitácora).
"""

from __future__ import annotations

from django.core.cache import cache

from core.cache.redis_cache import CACHE_GENERATION_KEY
from core.services.analytics_service import invalidate_dashboard_cache
from core.services.duckdb_s3 import DuckDBS3Session

DIRECT_MANIFEST_KEY = "crimetrack:direct:manifest:version"


def bump_cache_generation() -> int:
    current = cache.get(CACHE_GENERATION_KEY) or 0
    new_gen = int(current) + 1
    cache.set(CACHE_GENERATION_KEY, new_gen, None)
    cache.delete(DIRECT_MANIFEST_KEY)
    return new_gen


def invalidate_after_etl(*, refresh_dashboard: bool = True) -> dict[str, int]:
    """
    Llamar al finalizar ETL Celery o materialización OLAP masiva.
    Invalida expedientes/admin cacheados y sesión DuckDB in-process.
    """
    generation = bump_cache_generation()
    invalidate_dashboard_cache()
    DuckDBS3Session.reset_shared()

    if refresh_dashboard:
        try:
            from packages.dashboard_analitica.services.summary_materializer import (
                materialize_dashboard_summary,
                refresh_investigation_dashboard_metrics,
            )

            materialize_dashboard_summary()
            refresh_investigation_dashboard_metrics()
        except Exception:
            pass

    return {"cache_generation": generation}
