"""
Tareas Celery — generacion masiva Faker sin bloquear Django.
"""

from __future__ import annotations

from typing import Any

from celery import shared_task
from django.core.cache import cache

from core.cache.invalidation import invalidate_after_etl
from core.services.analytics_service import invalidate_dashboard_cache
from core.services.faker_bulk import bulk_insert_crimes_220k
from core.services.faker_realistic import bulk_insert_realistic_crimes

PROGRESS_TTL = 3600 * 6


def _progress_key(task_id: str) -> str:
    return f"crimetrack:faker:progress:{task_id}"


def _set_progress(task_id: str, data: dict[str, Any]) -> None:
    cache.set(_progress_key(task_id), data, PROGRESS_TTL)


@shared_task(bind=True, name="core.generate_fake_crimes")
def generate_fake_crimes_task(self, total_count: int) -> dict[str, Any]:
    task_id = self.request.id

    def on_progress(state: dict[str, Any]) -> None:
        _set_progress(
            task_id,
            {
                "status": "running",
                "task_id": task_id,
                **state,
            },
        )

    _set_progress(
        task_id,
        {
            "status": "running",
            "task_id": task_id,
            "done": 0,
            "total": total_count,
            "created": 0,
            "errors": 0,
            "percent": 0,
        },
    )

    try:
        result = bulk_insert_crimes_220k(
            total_count, on_progress=on_progress, workers=32
        )
        failed = not result.get("success")
        payload = {
            "status": "failed" if failed else "completed",
            "task_id": task_id,
            "percent": 100,
            "done": total_count,
            "total": total_count,
            "created": result.get("raw", {}).get("created", result.get("inserted_facts", 0)),
            "errors": result.get("raw", {}).get("errors", 0),
            "result": result,
        }
        if failed:
            msgs = result.get("error_messages") or []
            payload["error"] = msgs[0] if msgs else result.get("message", "No se insertó ningún registro")
        _set_progress(task_id, payload)
        invalidate_after_etl(refresh_dashboard=False)
        return payload
    except Exception as exc:
        payload = {
            "status": "failed",
            "task_id": task_id,
            "error": str(exc),
        }
        _set_progress(task_id, payload)
        raise


@shared_task(bind=True, name="core.generate_realistic_crimes")
def generate_realistic_crimes_task(self, total_count: int) -> dict[str, Any]:
    task_id = self.request.id

    def on_progress(state: dict[str, Any]) -> None:
        _set_progress(
            task_id,
            {"status": "running", "task_id": task_id, **state},
        )

    _set_progress(
        task_id,
        {
            "status": "running",
            "task_id": task_id,
            "done": 0,
            "total": total_count,
            "created": 0,
            "errors": 0,
            "percent": 0,
            "realistic": True,
        },
    )

    try:
        result = bulk_insert_realistic_crimes(
            total_count, on_progress=on_progress, workers=32
        )
        failed = not result.get("success")
        payload = {
            "status": "failed" if failed else "completed",
            "task_id": task_id,
            "percent": 100,
            "done": total_count,
            "total": total_count,
            "realistic": True,
            "created": result.get("created", 0),
            "errors": result.get("errors", 0),
            "result": result,
        }
        if failed:
            msgs = result.get("error_messages") or []
            payload["error"] = msgs[0] if msgs else result.get("message", "No se insertó ningún registro")
        _set_progress(task_id, payload)
        return payload
    except Exception as exc:
        payload = {"status": "failed", "task_id": task_id, "error": str(exc)}
        _set_progress(task_id, payload)
        raise


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


@shared_task(bind=True, name="core.run_etl_to_minio")
def run_etl_to_minio_task(self, export_raw_copy: bool = True) -> dict[str, Any]:
    from core.etl.star_schema import run_etl_pb_to_minio

    task_id = self.request.id
    key = f"crimetrack:etl:progress:{task_id}"

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
        {"status": "running", "task_id": task_id, "percent": 0, "message": "Iniciando ETL..."},
        PROGRESS_TTL,
    )
    try:
        result = run_etl_pb_to_minio(
            export_raw_copy=export_raw_copy, on_progress=on_progress
        )
        cache.set(
            key,
            {
                "status": "completed",
                "task_id": task_id,
                "percent": 100,
                "result": result,
                "message": result.get("message", "ETL completado"),
            },
            PROGRESS_TTL,
        )
        meta = invalidate_after_etl(refresh_dashboard=True)
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result,
            "cache_generation": meta["cache_generation"],
        }
    except Exception as exc:
        cache.set(
            key,
            {"status": "failed", "task_id": task_id, "error": str(exc), "percent": 0},
            PROGRESS_TTL,
        )
        raise
