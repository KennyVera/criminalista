"""
Restauración ZIP + ETL automático con progreso en caché y cancelación con rollback.
"""

from __future__ import annotations

import io
import threading
import uuid
import zipfile
from typing import Any, Callable

import pandas as pd
from django.core.cache import cache

from core.etl.star_schema import run_etl_pb_to_minio
from core.services.analytics_service import invalidate_dashboard_cache
from core.services.minio_store import MinioParquetStore
from packages.administracion_sistema.services.backups_admin import (
    ADMIN_TABLES,
    FULL_TABLES,
    BackupsAdminService,
)
from packages.dashboard_analitica.services.summary_materializer import (
    materialize_dashboard_summary,
)

PROGRESS_TTL = 3600 * 2
ROLLBACK_ROOT = "datasets/_restore_rollback"
ProgressFn = Callable[[dict[str, Any]], None]


class RestoreCancelled(Exception):
    """Cancelación solicitada por el usuario."""


def progress_cache_key(task_id: str) -> str:
    return f"crimetrack:restore-etl:{task_id}"


def cancel_cache_key(task_id: str) -> str:
    return f"crimetrack:restore-etl-cancel:{task_id}"


def get_restore_progress(task_id: str) -> dict[str, Any]:
    data = cache.get(progress_cache_key(task_id))
    if data:
        return data
    return {"status": "pending", "task_id": task_id, "percent": 0}


def _set_progress(task_id: str, payload: dict[str, Any]) -> None:
    cache.set(progress_cache_key(task_id), {"task_id": task_id, **payload}, PROGRESS_TTL)


def request_cancel_restore(task_id: str) -> dict[str, Any]:
    """Marca la tarea para cancelación; el worker hará rollback y detendrá el ETL."""
    progress = get_restore_progress(task_id)
    status = progress.get("status", "pending")
    if status in ("completed", "failed", "cancelled"):
        return {
            "task_id": task_id,
            "cancel_requested": False,
            "message": "La tarea ya finalizó.",
            "status": status,
        }
    cache.set(cancel_cache_key(task_id), True, PROGRESS_TTL)
    _set_progress(
        task_id,
        {
            "status": "cancelling",
            "percent": progress.get("percent", 0),
            "message": "Cancelando… revirtiendo datos al estado anterior.",
            "phase": "cancelling",
        },
    )
    return {
        "task_id": task_id,
        "cancel_requested": True,
        "message": "Cancelación en curso. Los datos volverán al estado previo.",
    }


def is_cancelled(task_id: str) -> bool:
    return bool(cache.get(cancel_cache_key(task_id)))


def _check_cancelled(task_id: str) -> None:
    if is_cancelled(task_id):
        raise RestoreCancelled("Operación cancelada por el usuario.")


def _delete_s3_prefix(client: Any, bucket: str, prefix: str) -> int:
    deleted = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        contents = page.get("Contents", [])
        if not contents:
            continue
        keys = [{"Key": o["Key"]} for o in contents]
        client.delete_objects(Bucket=bucket, Delete={"Objects": keys})
        deleted += len(keys)
    return deleted


def _copy_s3_prefix(client: Any, bucket: str, src_prefix: str, dst_prefix: str) -> int:
    copied = 0
    src = src_prefix if src_prefix.endswith("/") else f"{src_prefix}/"
    dst_base = dst_prefix if dst_prefix.endswith("/") else f"{dst_prefix}/"
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=src):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel = key[len(src) :] if key.startswith(src) else key.split("/")[-1]
            dst_key = f"{dst_base}{rel}"
            client.copy_object(
                Bucket=bucket,
                Key=dst_key,
                CopySource={"Bucket": bucket, "Key": key},
            )
            copied += 1
    return copied


def _write_df_to_s3(client: Any, bucket: str, key: str, df: pd.DataFrame) -> None:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, compression="snappy")
    buffer.seek(0)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )


class RestoreRollback:
    """Copias en MinIO del estado previo a la restauración."""

    def __init__(self, backups: BackupsAdminService, task_id: str) -> None:
        self.backups = backups
        self.task_id = task_id
        self.client = backups._s3
        self.bucket = backups._bucket
        self.base = f"{ROLLBACK_ROOT}/{task_id}"
        self.touched_tx: list[str] = []
        self.touched_admin: list[str] = []
        self.star_snapshotted = False

    def _tx_snap_key(self, table: str) -> str:
        return f"{self.base}/tx/{table}.parquet"

    def _admin_snap_key(self, table: str) -> str:
        return f"{self.base}/admin/{table}.parquet"

    def _star_snap_prefix(self) -> str:
        return f"{self.base}/star/"

    def snapshot_tx(self, table: str) -> None:
        df = self.backups.tx.read_table(table)
        _write_df_to_s3(self.client, self.bucket, self._tx_snap_key(table), df)

    def snapshot_admin(self, table: str) -> None:
        df = self.backups.admin.read_table(table)
        _write_df_to_s3(self.client, self.bucket, self._admin_snap_key(table), df)

    def snapshot_star_schema(self) -> None:
        star = MinioParquetStore()
        src = star.prefix if star.prefix.endswith("/") else f"{star.prefix}/"
        dst = self._star_snap_prefix()
        _copy_s3_prefix(self.client, self.bucket, src, dst)
        self.star_snapshotted = True

    def rollback(self) -> dict[str, Any]:
        restored_tx: list[str] = []
        restored_admin: list[str] = []

        for table in self.touched_tx:
            try:
                obj = self.client.get_object(
                    Bucket=self.bucket, Key=self._tx_snap_key(table)
                )
                df = pd.read_parquet(io.BytesIO(obj["Body"].read()))
                self.backups.tx.write_table(table, df)
                restored_tx.append(table)
            except Exception:
                pass

        for table in self.touched_admin:
            try:
                obj = self.client.get_object(
                    Bucket=self.bucket, Key=self._admin_snap_key(table)
                )
                df = pd.read_parquet(io.BytesIO(obj["Body"].read()))
                self.backups.admin.write_table(table, df)
                restored_admin.append(table)
            except Exception:
                pass

        if self.star_snapshotted:
            star = MinioParquetStore()
            live = star.prefix if star.prefix.endswith("/") else f"{star.prefix}/"
            _delete_s3_prefix(self.client, self.bucket, live)
            _copy_s3_prefix(
                self.client, self.bucket, self._star_snap_prefix(), live
            )
            star.invalidate_cache()

        invalidate_dashboard_cache()
        self.cleanup()
        return {
            "restored_transaccional": restored_tx,
            "restored_administracion": restored_admin,
            "star_rolled_back": self.star_snapshotted,
        }

    def cleanup(self) -> None:
        _delete_s3_prefix(self.client, self.bucket, f"{self.base}/")
        cache.delete(cancel_cache_key(self.task_id))


def run_restore_and_etl(
    zip_bytes: bytes,
    *,
    ejecutado_por: str,
    task_id: str,
    export_raw_copy: bool = False,
    rollback: RestoreRollback | None = None,
) -> dict[str, Any]:
    backups = BackupsAdminService()
    rollback = rollback or RestoreRollback(backups, task_id)

    def emit(percent: int, message: str, phase: str, **extra: Any) -> None:
        _set_progress(
            task_id,
            {
                "status": "running",
                "percent": min(100, max(0, percent)),
                "message": message,
                "phase": phase,
                **extra,
            },
        )

    def abort_if_cancelled() -> None:
        _check_cancelled(task_id)

    emit(2, "Guardando copia de seguridad del estado actual...", "snapshot")

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        has_analytics = backups.zip_has_analytics(zf)
        parquet_names = [n for n in zf.namelist() if n.endswith(".parquet")]
        tx_tables = set(FULL_TABLES)
        admin_tables = set(ADMIN_TABLES)
        tables_to_snap_tx: set[str] = set()
        tables_to_snap_admin: set[str] = set()

        for name in parquet_names:
            base = name.replace("\\", "/").split("/")[-1].replace(".parquet", "")
            if base in tx_tables:
                tables_to_snap_tx.add(base)
            elif base in admin_tables:
                tables_to_snap_admin.add(base)

        for t in tables_to_snap_tx:
            abort_if_cancelled()
            rollback.snapshot_tx(t)
        for t in tables_to_snap_admin:
            abort_if_cancelled()
            rollback.snapshot_admin(t)
        if not has_analytics:
            abort_if_cancelled()
            rollback.snapshot_star_schema()

        abort_if_cancelled()
        emit(4, "Analizando archivo ZIP...", "init")
        total = max(len(parquet_names), 1)
        emit(5, f"Restaurando {total} tablas desde ZIP...", "restore")

        restored_tx: list[str] = []
        restored_admin: list[str] = []
        errors: list[str] = []
        analytics_objects = 0

        for idx, name in enumerate(parquet_names):
            abort_if_cancelled()
            parts = name.replace("\\", "/").split("/")
            base = parts[-1].replace(".parquet", "")
            folder = parts[0] if len(parts) > 1 else ""
            pct_restore = 5 + int(20 * (idx + 1) / total)
            emit(pct_restore, f"Restaurando {base}...", "restore", table=base)
            try:
                df = pd.read_parquet(io.BytesIO(zf.read(name)))
            except Exception as exc:
                errors.append(f"{name}: {exc}")
                continue

            if folder == "transaccional" or (
                folder != "administracion" and base in tx_tables
            ):
                try:
                    backups.tx.write_table(base, df)
                    rollback.touched_tx.append(base)
                    if base not in restored_tx:
                        restored_tx.append(base)
                except Exception as exc:
                    errors.append(f"tx/{base}: {exc}")
            elif folder == "administracion" or base in admin_tables:
                try:
                    backups.admin.write_table(base, df)
                    rollback.touched_admin.append(base)
                    if base not in restored_admin:
                        restored_admin.append(base)
                except Exception as exc:
                    errors.append(f"admin/{base}: {exc}")
            elif base in tx_tables:
                try:
                    backups.tx.write_table(base, df)
                    rollback.touched_tx.append(base)
                    if base not in restored_tx:
                        restored_tx.append(base)
                except Exception as exc:
                    errors.append(f"tx/{base}: {exc}")

        if has_analytics:
            abort_if_cancelled()
            emit(22, "Restaurando capa analítica (OLAP) desde ZIP...", "restore_analytics")
            analytics_objects, a_err = backups.restore_analytics_from_zip(zf)
            errors.extend(a_err)
            rollback.star_snapshotted = True

    abort_if_cancelled()

    restore_ok = bool(restored_tx or restored_admin)
    if not restore_ok:
        rollback.rollback()
        raise RuntimeError(
            "No se pudo restaurar ninguna tabla. " + "; ".join(errors[:3])
        )

    emit(
        25,
        (
            f"Restauración OK ({len(restored_tx)} TX + {len(restored_admin)} admin"
            f"{f', {analytics_objects} objs analítica' if has_analytics else ''})."
        ),
        "restore_done",
        restored_transaccional=restored_tx,
        restored_administracion=restored_admin,
        restored_analytics_objects=analytics_objects,
    )

    etl_result: dict[str, Any] | None = None
    summary_result: dict[str, Any] | None = None

    if has_analytics:
        abort_if_cancelled()
        emit(90, "Capa analítica restaurada desde ZIP (sin ETL PocketBase).", "summary")
        if "app_dashboard_summary" not in restored_tx:
            emit(92, "Regenerando resumen del dashboard...", "summary")
            summary_result = materialize_dashboard_summary()
    else:
        abort_if_cancelled()
        emit(26, "Resguardando modelo analítico actual...", "snapshot")
        rollback.snapshot_star_schema()

        def etl_progress(state: dict[str, Any]) -> None:
            abort_if_cancelled()
            etl_pct = int(state.get("percent", 0))
            combined = 25 + int(0.74 * etl_pct)
            emit(
                combined,
                state.get("message", "ETL modelo estrella..."),
                state.get("phase", "etl"),
            )

        try:
            etl_result = run_etl_pb_to_minio(
                export_raw_copy=export_raw_copy,
                on_progress=etl_progress,
                should_cancel=lambda: is_cancelled(task_id),
            )
            summary_result = materialize_dashboard_summary()
        except RestoreCancelled:
            raise
        except RuntimeError as exc:
            if is_cancelled(task_id) or "cancelado" in str(exc).lower():
                raise RestoreCancelled(str(exc)) from exc
            raise RuntimeError(f"ETL falló tras restaurar: {exc}") from exc

    invalidate_dashboard_cache()
    rollback.cleanup()

    if has_analytics:
        msg = "Restauración completada (OLAP incluido en ZIP). Ya puede iniciar sesión."
    else:
        msg = "Restauración y ETL completados. Ya puede iniciar sesión."

    result = {
        "success": True,
        "message": msg,
        "restore": {
            "restored_transaccional": restored_tx,
            "restored_administracion": restored_admin,
            "restored_analytics_objects": analytics_objects,
            "errors": errors,
            "skipped_etl": has_analytics,
        },
        "etl": etl_result,
        "dashboard_summary": summary_result,
    }

    _set_progress(
        task_id,
        {
            "status": "completed",
            "percent": 100,
            "phase": "done",
            "message": result["message"],
            "result": result,
        },
    )
    return result


def _handle_cancelled(task_id: str, rollback: RestoreRollback | None) -> None:
    info = rollback.rollback() if rollback else {}
    _set_progress(
        task_id,
        {
            "status": "cancelled",
            "percent": 0,
            "phase": "cancelled",
            "message": (
                "Restauración cancelada. Se dejó MinIO como antes de iniciar el proceso."
            ),
            "rollback": info,
        },
    )


def enqueue_restore_and_etl(
    zip_bytes: bytes,
    *,
    ejecutado_por: str,
    export_raw_copy: bool = False,
) -> str:
    """Ejecuta en segundo plano (hilo) y devuelve task_id para consultar progreso."""
    task_id = str(uuid.uuid4())
    cache.delete(cancel_cache_key(task_id))
    _set_progress(
        task_id,
        {
            "status": "running",
            "percent": 0,
            "message": "Iniciando restauración...",
            "phase": "queued",
        },
    )

    def worker() -> None:
        backups = BackupsAdminService()
        rollback = RestoreRollback(backups, task_id)
        try:
            run_restore_and_etl(
                zip_bytes,
                ejecutado_por=ejecutado_por,
                task_id=task_id,
                export_raw_copy=export_raw_copy,
                rollback=rollback,
            )
        except RestoreCancelled:
            _handle_cancelled(task_id, rollback)
        except Exception as exc:
            if is_cancelled(task_id) and rollback is not None:
                _handle_cancelled(task_id, rollback)
                return
            _set_progress(
                task_id,
                {
                    "status": "failed",
                    "percent": 0,
                    "phase": "error",
                    "message": str(exc),
                    "error": str(exc),
                },
            )

    threading.Thread(target=worker, daemon=True).start()
    return task_id
