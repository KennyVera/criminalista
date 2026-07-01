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


def sync_progress_key(task_id: str) -> str:
    return f"crimetrack:sync:progress:{task_id}"


def etl_progress_key(task_id: str) -> str:
    """Alias histórico (misma clave que sync)."""
    return sync_progress_key(task_id)


def set_job_progress(key: str, payload: dict[str, Any]) -> None:
    cache.set(key, payload, PROGRESS_TTL)


def get_job_progress(key: str) -> dict[str, Any] | None:
    return cache.get(key)


SYNC_CELERY_TASK = "core.sync_pocketbase"
SYNC_CELERY_TASK_LEGACY = "core.run_etl_to_minio"


def _celery_available() -> bool:
    try:
        from crimetrack.celery import app as celery_app

        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1)
        return True
    except Exception:
        return False


def _celery_worker_has_task(task_name: str) -> bool:
    """True si algún worker reporta la tarea registrada (evita encolar tareas huérfanas)."""
    try:
        from crimetrack.celery import app as celery_app

        inspect = celery_app.control.inspect(timeout=2.0)
        registered = inspect.registered() or {}
        return any(task_name in (tasks or []) for tasks in registered.values())
    except Exception:
        return False


def _celery_sync_ready() -> bool:
    if not _celery_available():
        return False
    return _celery_worker_has_task(SYNC_CELERY_TASK) or _celery_worker_has_task(
        SYNC_CELERY_TASK_LEGACY
    )


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


def enqueue_sync_job(
    *,
    mode: str = "auto",
    export_raw_copy: bool = True,
    per_page: int = 500,
    cantidad_registros: int | None = None,
) -> dict[str, Any]:
    """Encola sincronización PocketBase -> MinIO."""
    if _celery_sync_ready():
        try:
            from core.tasks import run_etl_to_minio_task, sync_pocketbase_task

            kwargs = {
                "mode": mode,
                "export_raw_copy": export_raw_copy,
                "per_page": per_page,
                "cantidad_registros": cantidad_registros,
            }
            if _celery_worker_has_task(SYNC_CELERY_TASK):
                task = sync_pocketbase_task.delay(**kwargs)
            else:
                task = run_etl_to_minio_task.delay(**kwargs)
            return {
                "task_id": task.id,
                "status": "queued",
                "backend": "celery",
                "mode": mode,
            }
        except Exception:
            pass

    task_id = str(uuid.uuid4())
    key = sync_progress_key(task_id)

    def work() -> None:
        from core.cache.invalidation import invalidate_after_etl
        from core.services.pb_sync_service import run_pocketbase_sync

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
                from core.tasks import refresh_dashboard_summary_task

                refresh_dashboard_summary_task.delay()
            except Exception:
                pass
        invalidate_after_etl(refresh_dashboard=not defer_dashboard)
        set_job_progress(
            key,
            {
                "status": "completed",
                "task_id": task_id,
                "percent": 100,
                "result": result,
                "message": result.get("message", "Sincronización completada"),
                "sync_mode": result.get("sync_mode"),
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
            "message": "Iniciando sincronización...",
            "backend": "thread",
            "mode": mode,
        },
    )
    return {"task_id": task_id, "status": "queued", "backend": "thread", "mode": mode}


def enqueue_etl_job(*, export_raw_copy: bool = True) -> dict[str, Any]:
    """Compatibilidad: delega al pipeline de sincronización."""
    return enqueue_sync_job(mode="auto", export_raw_copy=export_raw_copy)


def resolve_job_status(task_id: str) -> dict[str, Any]:
    """Consulta progreso sync/ETL o Celery AsyncResult."""
    data = get_job_progress(sync_progress_key(task_id))
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
            err = str(result.result)
            if err.strip("'\"") in (SYNC_CELERY_TASK, SYNC_CELERY_TASK_LEGACY):
                err = (
                    "El worker de Celery no tiene registrada la tarea de sincronización. "
                    "Reinicia el contenedor crimetrack-celery o vuelve a intentar "
                    "(se usará hilo en segundo plano)."
                )
            return {
                "status": "failed",
                "task_id": task_id,
                "error": err,
            }
        return {"status": result.state.lower(), "task_id": task_id}
    except Exception:
        pass

    return {"status": "pending", "task_id": task_id}
