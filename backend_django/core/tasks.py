"""
Tareas Celery — sincronización PocketBase -> MinIO sin bloquear Django.
"""

from __future__ import annotations

from typing import Any

from celery import shared_task
from django.core.cache import cache

from core.cache.invalidation import invalidate_after_etl

PROGRESS_TTL = 3600 * 6


def _sync_progress_key(task_id: str) -> str:
    return f"crimetrack:sync:progress:{task_id}"


def _run_sync_job(
    task_id: str,
    *,
    mode: str = "auto",
    export_raw_copy: bool = True,
    per_page: int = 500,
    cantidad_registros: int | None = None,
) -> dict[str, Any]:
    from core.services.pb_sync_service import run_pocketbase_sync

    key = _sync_progress_key(task_id)

    def on_progress(state: dict) -> None:
        cache.set(
            key,
            {
                "status": "running",
                "task_id": task_id,
                "percent": state.get("percent", 0),
                "phase": state.get("phase", ""),
                "message": state.get("message", ""),
                **state,
            },
            PROGRESS_TTL,
        )

    cache.set(
        key,
        {
            "status": "running",
            "task_id": task_id,
            "percent": 0,
            "message": "Iniciando sincronización...",
            "mode": mode,
        },
        PROGRESS_TTL,
    )
    result = run_pocketbase_sync(
        mode=mode,
        export_raw_copy=export_raw_copy,
        per_page=per_page,
        cantidad_registros=cantidad_registros,
        on_progress=on_progress,
    )
    defer_dashboard = bool(result.get("dashboard_deferred"))
    if defer_dashboard:
        try:
            refresh_dashboard_summary_task.delay()
        except Exception:
            pass
    cache.set(
        key,
        {
            "status": "completed",
            "task_id": task_id,
            "percent": 100,
            "result": result,
            "message": result.get("message", "Sincronización completada"),
            "sync_mode": result.get("sync_mode"),
        },
        PROGRESS_TTL,
    )
    meta = invalidate_after_etl(refresh_dashboard=not defer_dashboard)
    return {
        "status": "completed",
        "task_id": task_id,
        "result": result,
        "cache_generation": meta["cache_generation"],
    }


@shared_task(name="core.refresh_dashboard_summary")
def refresh_dashboard_summary_task() -> dict[str, Any]:
    """Cron/Celery beat: actualiza app_dashboard_summary desde MinIO OLAP."""
    from packages.dashboard_analitica.services.summary_materializer import (
        materialize_dashboard_summary,
    )

    return materialize_dashboard_summary()


@shared_task(name="core.run_scheduled_backups")
def run_scheduled_backups_task() -> dict[str, Any]:
    from packages.administracion_sistema.services.backups_admin import BackupsAdminService

    results = BackupsAdminService().run_due_scheduled()
    return {"ejecutados": len(results), "resultados": results}


@shared_task(name="core.run_scheduled_reports")
def run_scheduled_reports_task() -> dict[str, Any]:
    """Celery beat: envía por correo los reportes programados vencidos (CU-O38)."""
    from packages.reporteria_exportacion.services.report_service import ReportService

    results = ReportService().run_due_scheduled()
    return {"ejecutados": len(results), "resultados": results}


@shared_task(bind=True, name="core.sync_pocketbase")
def sync_pocketbase_task(
    self,
    *,
    mode: str = "auto",
    export_raw_copy: bool = True,
    per_page: int = 500,
    cantidad_registros: int | None = None,
) -> dict[str, Any]:
    try:
        return _run_sync_job(
            self.request.id,
            mode=mode,
            export_raw_copy=export_raw_copy,
            per_page=per_page,
            cantidad_registros=cantidad_registros,
        )
    except Exception as exc:
        cache.set(
            _sync_progress_key(self.request.id),
            {"status": "failed", "task_id": self.request.id, "error": str(exc), "percent": 0},
            PROGRESS_TTL,
        )
        raise


@shared_task(bind=True, name="core.run_etl_to_minio")
def run_etl_to_minio_task(
    self,
    export_raw_copy: bool = True,
    *,
    mode: str = "auto",
    per_page: int = 500,
    cantidad_registros: int | None = None,
) -> dict[str, Any]:
    """Alias histórico de sincronización PocketBase -> MinIO (compat. workers antiguos)."""
    try:
        return _run_sync_job(
            self.request.id,
            mode=mode,
            export_raw_copy=export_raw_copy,
            per_page=per_page,
            cantidad_registros=cantidad_registros,
        )
    except Exception as exc:
        cache.set(
            _sync_progress_key(self.request.id),
            {"status": "failed", "task_id": self.request.id, "error": str(exc), "percent": 0},
            PROGRESS_TTL,
        )
        raise
