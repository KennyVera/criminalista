"""
Encolado unificado: Celery si está disponible; si no, hilo en segundo plano + caché Django.
Libera la respuesta HTTP de inmediato (202 + task_id).
"""

from __future__ import annotations

import threading
import uuid
from typing import Any, Callable

from django.core.cache import cache

PROGRESS_TTL = 3600 * 6


def faker_progress_key(task_id: str) -> str:
    return f"crimetrack:faker:progress:{task_id}"


def etl_progress_key(task_id: str) -> str:
    return f"crimetrack:etl:progress:{task_id}"


def set_job_progress(key: str, payload: dict[str, Any]) -> None:
    cache.set(key, payload, PROGRESS_TTL)


def get_job_progress(key: str) -> dict[str, Any] | None:
    return cache.get(key)


def _celery_available() -> bool:
    try:
        from crimetrack.celery import app as celery_app

        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1)
        return True
    except Exception:
        return False


def _run_in_thread(
    target: Callable[[], None],
    *,
    progress_key: str,
    task_id: str,
    initial: dict[str, Any],
) -> None:
    set_job_progress(progress_key, initial)

    def wrapper() -> None:
        try:
            target()
        except Exception as exc:
            set_job_progress(
                progress_key,
                {
                    "status": "failed",
                    "task_id": task_id,
                    "error": str(exc),
                    "percent": 0,
                },
            )

    threading.Thread(target=wrapper, daemon=True).start()


def enqueue_faker_job(count: int, *, realistic: bool = False) -> dict[str, Any]:
    """Encola generación Faker; retorna task_id para polling."""
    if _celery_available():
        try:
            if realistic:
                from core.tasks import generate_realistic_crimes_task

                task = generate_realistic_crimes_task.delay(count)
            else:
                from core.tasks import generate_fake_crimes_task

                task = generate_fake_crimes_task.delay(count)
            return {
                "task_id": task.id,
                "status": "queued",
                "backend": "celery",
                "total": count,
                "realistic": realistic,
            }
        except Exception:
            pass

    task_id = str(uuid.uuid4())
    key = faker_progress_key(task_id)

    def work() -> None:
        from core.services.faker_bulk import bulk_insert_crimes_220k
        from core.services.faker_realistic import bulk_insert_realistic_crimes

        def on_progress(state: dict[str, Any]) -> None:
            set_job_progress(
                key,
                {"status": "running", "task_id": task_id, **state},
            )

        if realistic:
            result = bulk_insert_realistic_crimes(count, on_progress=on_progress)
        else:
            result = bulk_insert_crimes_220k(count, on_progress=on_progress)

        set_job_progress(
            key,
            {
                "status": "completed" if result.get("success") else "failed",
                "task_id": task_id,
                "percent": 100,
                "done": count,
                "total": count,
                "result": result,
            },
        )

    _run_in_thread(
        work,
        progress_key=key,
        task_id=task_id,
        initial={
            "status": "running",
            "task_id": task_id,
            "done": 0,
            "total": count,
            "created": 0,
            "errors": 0,
            "percent": 0,
            "realistic": realistic,
            "backend": "thread",
        },
    )
    return {
        "task_id": task_id,
        "status": "queued",
        "backend": "thread",
        "total": count,
        "realistic": realistic,
    }


def enqueue_etl_job(*, export_raw_copy: bool = True) -> dict[str, Any]:
    if _celery_available():
        try:
            from core.tasks import run_etl_to_minio_task

            task = run_etl_to_minio_task.delay(export_raw_copy=export_raw_copy)
            return {
                "task_id": task.id,
                "status": "queued",
                "backend": "celery",
            }
        except Exception:
            pass

    task_id = str(uuid.uuid4())
    key = etl_progress_key(task_id)

    def work() -> None:
        from core.etl.star_schema import run_etl_pb_to_minio
        from core.services.analytics_service import invalidate_dashboard_cache

        def on_progress(state: dict[str, Any]) -> None:
            set_job_progress(
                key,
                {
                    "status": "running",
                    "task_id": task_id,
                    "percent": state.get("percent", 0),
                    "phase": state.get("phase", ""),
                    "message": state.get("message", ""),
                    **state,
                },
            )

        result = run_etl_pb_to_minio(
            export_raw_copy=export_raw_copy, on_progress=on_progress
        )
        invalidate_dashboard_cache()
        set_job_progress(
            key,
            {
                "status": "completed",
                "task_id": task_id,
                "percent": 100,
                "result": result,
                "message": result.get("message", "ETL completado"),
            },
        )

    _run_in_thread(
        work,
        progress_key=key,
        task_id=task_id,
        initial={
            "status": "running",
            "task_id": task_id,
            "percent": 0,
            "message": "Iniciando ETL...",
            "backend": "thread",
        },
    )
    return {"task_id": task_id, "status": "queued", "backend": "thread"}


def resolve_job_status(task_id: str) -> dict[str, Any]:
    """Consulta progreso faker, ETL o Celery AsyncResult."""
    for key_fn in (faker_progress_key, etl_progress_key):
        data = get_job_progress(key_fn(task_id))
        if data:
            return data

    try:
        from celery.result import AsyncResult

        from crimetrack.celery import app as celery_app

        result = AsyncResult(task_id, app=celery_app)
        if result.state == "PENDING":
            return {"status": "pending", "task_id": task_id}
        if result.ready():
            if result.successful():
                payload = result.result or {"status": "completed"}
                if isinstance(payload, dict):
                    payload.setdefault("task_id", task_id)
                return payload
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(result.result),
            }
        return {"status": result.state.lower(), "task_id": task_id}
    except Exception:
        pass

    return {"status": "pending", "task_id": task_id}
