"""
Materializa métricas del dashboard en app_dashboard_summary (DuckDB offline → lectura <1ms).
"""

from __future__ import annotations

import time
from typing import Any

from core.services.analytics_service import invalidate_dashboard_cache
from packages.dashboard_analitica.services.analytics_engine import DashboardAnalyticsEngine
from packages.dashboard_analitica.services.dashboard_summary_store import DashboardSummaryStore
from packages.dashboard_analitica.services.detective_ranking_service import live_investigation_metrics


def _build_agg_rollups(engine: DashboardAnalyticsEngine) -> list[dict[str, Any]]:
    """Rollups compactos para filtros sin escanear 300k en cada request."""
    con = engine.connection()
    fact = engine._fact_parquet_source()
    dist = engine._dim_parquet("dim_distrito_policial")
    tipo = engine._dim_parquet("dim_tipo_crimen")
    tiempo = engine._dim_parquet("dim_tiempo")
    sql = f"""
        SELECT
            CAST(d.district AS VARCHAR) AS distrito,
            CAST(d.beat AS VARCHAR) AS beat,
            CAST(t.primary_type AS VARCHAR) AS tipo,
            CAST(ti.year AS VARCHAR) AS anio,
            CAST(ti.month AS VARCHAR) AS mes,
            COUNT(*)::BIGINT AS total
        FROM read_parquet('{fact}') AS f
        INNER JOIN read_parquet('{dist}') AS d
            ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
        INNER JOIN read_parquet('{tipo}') AS t
            ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(t.id AS BIGINT)
        INNER JOIN read_parquet('{tiempo}') AS ti
            ON CAST(f.fk_tiempo AS BIGINT) = CAST(ti.id AS BIGINT)
        GROUP BY d.district, d.beat, t.primary_type, ti.year, ti.month
    """
    df = con.execute(sql).fetchdf()
    return df.to_dict(orient="records")


def refresh_investigation_dashboard_metrics(*, ranking_limit: int = 15) -> None:
    """
    Actualiza ranking y tasa de resolución en app_dashboard_summary sin re-materializar OLAP.
    Invocar tras bitácora, asignaciones o reasignaciones.
    """
    live = live_investigation_metrics(ranking_limit=ranking_limit)
    ranking_items = live["detective_ranking"]
    tasa = live["tasa_resolucion"]

    store = DashboardSummaryStore()
    store.upsert_payload("detective_ranking", {"items": ranking_items, "source": "live"})

    overview = store.get_payload("overview")
    if isinstance(overview, dict):
        patched = dict(overview)
        patched["detective_ranking"] = ranking_items
        op = dict(patched.get("operational_indicators") or {})
        op["tasa_resolucion"] = {**dict(op.get("tasa_resolucion") or {}), **tasa}
        patched["operational_indicators"] = op
        patched["investigation_metrics_live"] = True
        store.upsert_payload("overview", patched)

    operational = store.get_payload("operational")
    if isinstance(operational, dict):
        patched_op = dict(operational)
        patched_op["tasa_resolucion"] = {**dict(patched_op.get("tasa_resolucion") or {}), **tasa}
        store.upsert_payload("operational", patched_op)

    invalidate_dashboard_cache()


def materialize_dashboard_summary() -> dict[str, Any]:
    """
    Ejecuta agregaciones pesadas una vez y persiste en app_dashboard_summary.
    Invocar tras ETL, cron Celery o manage.py refresh_dashboard_summary.
    """
    t0 = time.perf_counter()
    engine = DashboardAnalyticsEngine()
    fact_count = engine.count_fact_crimes()

    overview = engine.build_dashboard_payload()
    overview["totals"]["crimes_220k"] = fact_count
    overview["totals"]["source"] = "minio_olap"
    overview["architecture"] = {
        "pocketbase": "solo OLTP (ingesta crimes_220k)",
        "minio": "Parquet OLAP + app_dashboard_summary",
        "read_path": "materialized_summary",
    }

    entries = {
        "overview": overview,
        "filter_options": engine.filter_options(),
        "heat_map": {"items": engine.heat_map_by_district(limit=15)},
        "detective_ranking": {"items": engine.detective_ranking(limit=10)},
        "operational": engine.operational_indicators(),
        "agg_rollups": _build_agg_rollups(engine),
    }

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    store = DashboardSummaryStore()
    store.replace_all(entries, filas_hechos=fact_count, duracion_ms=elapsed_ms)
    try:
        from core.cache.invalidation import bump_cache_generation

        bump_cache_generation()
    except Exception:
        pass
    invalidate_dashboard_cache()

    read_ms = store.read_timing_ms()
    return {
        "success": True,
        "filas_hechos": fact_count,
        "materialize_ms": elapsed_ms,
        "read_ms": read_ms,
        "keys": list(entries.keys()),
        "message": (
            f"Resumen dashboard actualizado ({fact_count:,} hechos, "
            f"materialización {elapsed_ms} ms, lectura {read_ms} ms)."
        ).replace(",", "."),
    }


def filtered_stats_from_summary(
    *,
    distrito: str | None = None,
    tipo: str | None = None,
    year: str | None = None,
    month: str | None = None,
) -> dict[str, Any]:
    """Filtra rollups precalculados en memoria (sin DuckDB ni PocketBase)."""
    store = DashboardSummaryStore()
    rollups = store.get_payload("agg_rollups") or []
    if not isinstance(rollups, list):
        rollups = []

    def match(row: dict) -> bool:
        if distrito and str(row.get("distrito", "")) != distrito and str(row.get("beat", "")) != distrito:
            return False
        if tipo and str(row.get("tipo", "")) != tipo:
            return False
        if year and str(row.get("anio", "")) != str(year):
            return False
        if month and str(row.get("mes", "")) != str(month):
            return False
        return True

    filtered = [r for r in rollups if match(r)]
    total = sum(int(r.get("total", 0) or 0) for r in filtered)

    by_tipo: dict[str, int] = {}
    by_anio: dict[str, int] = {}
    by_dist: dict[str, int] = {}
    for r in filtered:
        t = str(r.get("tipo", "—"))
        y = str(r.get("anio", "—"))
        d = str(r.get("distrito", r.get("beat", "—")))
        n = int(r.get("total", 0) or 0)
        by_tipo[t] = by_tipo.get(t, 0) + n
        by_anio[y] = by_anio.get(y, 0) + n
        by_dist[d] = by_dist.get(d, 0) + n

    filters = {
        k: v
        for k, v in {
            "distrito": distrito,
            "tipo": tipo,
            "year": year,
            "month": month,
        }.items()
        if v
    }

    return {
        "filters_applied": filters,
        "total_hechos": total,
        "por_tipo": [
            {"label": k, "value": v}
            for k, v in sorted(by_tipo.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
        "por_anio": [
            {"label": k, "value": v} for k, v in sorted(by_anio.items(), key=lambda x: x[0])
        ],
        "por_distrito": [
            {"district": k, "beat": "", "total_crimes": v}
            for k, v in sorted(by_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
        "source": "app_dashboard_summary",
    }
