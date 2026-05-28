from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from packages.administracion_sistema.storage import ADMIN_COLLECTIONS, SCHEMAS, AdminMinioStore
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

FULL_TABLES = [
    "app_roles",
    "app_usuarios",
    "app_sesiones_activas",
    "app_audit_logs",
    "app_involucrados",
    "app_caso_involucrado",
    "app_evidencias",
]

ADMIN_TABLES = list(ADMIN_COLLECTIONS)

INCREMENTAL_TABLES = [
    "app_sesiones_activas",
    "app_audit_logs",
]

MANIFEST_NAME = "crimetrack_manifest.json"
ETL_HINT = (
    "El modelo estrella (fact_crimes y dimensiones) no va en este ZIP; "
    "restáuralo ejecutando: python manage.py etl_pb_to_minio (requiere crimes_220k en PocketBase)."
)

FREQ_HOURS = {
    "horario": 24,
    "diario": 24,
    "semanal": 24 * 7,
    "mensual": 24 * 30,
}


class BackupsAdminService:
    def __init__(self) -> None:
        self.admin = AdminMinioStore()
        self.tx = TransactionalMinioStore()
        self._s3 = self.tx._client
        self._bucket = self.tx.bucket

    def _normalize_config_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        defaults = {
            "tipo_respaldo": "completo",
            "hora_programada": "02:00",
            "proxima_ejecucion": "",
        }
        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default
        return df

    def _ensure_historial_table(self) -> None:
        try:
            self.admin.read_table("sys_respaldos_historial")
        except Exception:
            self.admin.write_table(
                "sys_respaldos_historial",
                pd.DataFrame(columns=SCHEMAS["sys_respaldos_historial"]),
            )

    def get_config(self) -> list[dict[str, Any]]:
        df = self._normalize_config_df(self.admin.read_table("sys_respaldos_config"))
        return df.to_dict(orient="records")

    def create_config(self, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "nombre": str(data.get("nombre", "Respaldo programado")).strip(),
            "frecuencia": str(data.get("frecuencia", "diario")).strip().lower(),
            "destino_minio_prefix": str(data.get("destino_minio_prefix", "backups/daily")).strip(),
            "tipo_respaldo": str(data.get("tipo_respaldo", "completo")).strip().lower(),
            "hora_programada": str(data.get("hora_programada", "02:00")).strip(),
            "activo": bool(data.get("activo", True)),
            "ultima_ejecucion": "",
            "ultimo_estado": "Pendiente de primera ejecución",
            "proxima_ejecucion": self._calc_next_run(
                str(data.get("frecuencia", "diario")),
                str(data.get("hora_programada", "02:00")),
            ),
        }
        return self.admin.append_row("sys_respaldos_config", row)

    def update_config(self, config_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        allowed = (
            "nombre",
            "frecuencia",
            "destino_minio_prefix",
            "tipo_respaldo",
            "hora_programada",
            "activo",
            "ultima_ejecucion",
            "ultimo_estado",
            "proxima_ejecucion",
        )
        payload = {k: data[k] for k in allowed if k in data}
        if "frecuencia" in payload or "hora_programada" in payload:
            cfg = self.get_config()
            current = next((c for c in cfg if int(c["id"]) == config_id), {})
            freq = str(payload.get("frecuencia", current.get("frecuencia", "diario")))
            hora = str(payload.get("hora_programada", current.get("hora_programada", "02:00")))
            payload["proxima_ejecucion"] = self._calc_next_run(freq, hora)
        return self.admin.update_row("sys_respaldos_config", config_id, payload)

    def list_history(
        self, *, limit: int = 50, manual_only: bool = True
    ) -> list[dict[str, Any]]:
        """Por defecto solo ejecuciones manuales (botón Ejecutar en admin)."""
        self._ensure_historial_table()
        df = self.admin.read_table("sys_respaldos_historial")
        if df.empty:
            return []
        if manual_only and "es_manual" in df.columns:
            df = df[df["es_manual"].fillna(False).astype(bool)]
        if "iniciado_en" in df.columns:
            df = df.sort_values("iniciado_en", ascending=False)
        return df.head(limit).to_dict(orient="records")

    def list_failed_alerts(self, *, hours: int = 72) -> list[dict[str, Any]]:
        """HU-3: respaldos fallidos recientes para Comisario/Admin."""
        self._ensure_historial_table()
        df = self.admin.read_table("sys_respaldos_historial")
        if df.empty:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        items = []
        for row in df.to_dict(orient="records"):
            estado = str(row.get("estado", "")).lower()
            if estado not in ("fallido", "error", "failed"):
                continue
            started = row.get("iniciado_en") or row.get("finalizado_en") or ""
            try:
                dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            except ValueError:
                continue
            if dt >= cutoff:
                items.append(row)
        return sorted(items, key=lambda r: r.get("iniciado_en", ""), reverse=True)

    def run_due_scheduled(self) -> list[dict[str, Any]]:
        """Ejecuta respaldos programados vencidos (CU-17)."""
        results = []
        now = datetime.now(timezone.utc)
        for cfg in self.get_config():
            if not cfg.get("activo"):
                continue
            if not self._is_due(cfg, now):
                continue
            results.append(
                self.run_backup(
                    int(cfg["id"]),
                    manual=False,
                    ejecutado_por="sistema",
                )
            )
        return results

    def run_backup(
        self,
        config_id: int,
        *,
        manual: bool = True,
        ejecutado_por: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_historial_table()
        cfg_df = self._normalize_config_df(self.admin.read_table("sys_respaldos_config"))
        row = cfg_df[cfg_df["id"] == config_id]
        if row.empty:
            raise ValueError("Configuración de respaldo no encontrada")

        c = row.iloc[0].to_dict()
        tipo = str(c.get("tipo_respaldo", "completo")).lower()
        tables = INCREMENTAL_TABLES if tipo == "incremental" else FULL_TABLES
        prefix = str(c["destino_minio_prefix"])
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = f"{prefix}/{tipo}/{ts}/"
        iniciado = utc_now_iso()
        historial_id: int | None = None
        if manual:
            historial_id = self._append_history_start(
                c, tipo, dest, manual, ejecutado_por, iniciado
            )

        copied = 0
        errors: list[str] = []
        files_manifest: list[str] = []

        for table in tables:
            try:
                key = f"{dest}transaccional/{table}.parquet"
                self._put_parquet_key(key, self.tx.read_table(table))
                files_manifest.append(key)
                copied += 1
            except Exception as exc:
                errors.append(f"{table}: {exc}")

        if tipo == "completo":
            for table in ADMIN_TABLES:
                try:
                    key = f"{dest}administracion/{table}.parquet"
                    self._put_parquet_key(key, self.admin.read_table(table))
                    files_manifest.append(key)
                    copied += 1
                except Exception as exc:
                    errors.append(f"{table}: {exc}")

        manifest = {
            "version": 1,
            "tipo": tipo,
            "generado_en": iniciado,
            "destino_minio": dest,
            "tablas_transaccionales": tables,
            "tablas_administracion": ADMIN_TABLES if tipo == "completo" else [],
            "archivos": files_manifest,
            "nota_modelo_estrella": ETL_HINT,
        }
        self._s3.put_object(
            Bucket=self._bucket,
            Key=f"{dest}{MANIFEST_NAME}",
            Body=json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )

        success = copied > 0 and len(errors) == 0
        finalizado = utc_now_iso()
        if success:
            estado = "completado"
            detalle = f"OK — {copied} tablas ({tipo}) en {dest}"
        else:
            estado = "fallido"
            detalle = f"Error — copiadas {copied}/{len(tables)}. " + "; ".join(errors[:3])

        if historial_id is not None:
            self._finalize_history(historial_id, estado, detalle, copied, finalizado)
        freq = str(c.get("frecuencia", "diario"))
        hora = str(c.get("hora_programada", "02:00"))
        self.admin.update_row(
            "sys_respaldos_config",
            config_id,
            {
                "ultima_ejecucion": finalizado,
                "ultimo_estado": detalle,
                "proxima_ejecucion": self._calc_next_run(freq, hora, from_dt=now_dt()),
            },
        )

        if not success:
            self._notify_backup_failure(c, detalle)

        return {
            "success": success,
            "config_id": config_id,
            "tipo": tipo,
            "manual": manual,
            "destino": dest,
            "tablas_copiadas": copied,
            "tablas_objetivo": len(tables),
            "estado": estado,
            "detalle": detalle,
            "timestamp": ts,
            "historial_id": historial_id,
        }

    def _append_history_start(
        self,
        cfg: dict,
        tipo: str,
        dest: str,
        manual: bool,
        ejecutado_por: str | None,
        iniciado: str,
    ) -> int:
        row = {
            "fk_config": int(cfg["id"]),
            "nombre_config": str(cfg.get("nombre", "")),
            "tipo_respaldo": tipo,
            "frecuencia": str(cfg.get("frecuencia", "")),
            "destino": dest,
            "iniciado_en": iniciado,
            "finalizado_en": "",
            "estado": "en_progreso",
            "tablas_copiadas": 0,
            "detalle": "Ejecución iniciada",
            "es_manual": manual,
            "ejecutado_por": ejecutado_por or ("manual" if manual else "sistema"),
        }
        created = self.admin.append_row("sys_respaldos_historial", row)
        return int(created["id"])

    def _finalize_history(
        self,
        historial_id: int,
        estado: str,
        detalle: str,
        tablas: int,
        finalizado: str,
    ) -> None:
        self.admin.update_row(
            "sys_respaldos_historial",
            historial_id,
            {
                "estado": estado,
                "detalle": detalle,
                "tablas_copiadas": tablas,
                "finalizado_en": finalizado,
            },
        )

    def _put_parquet_key(self, key: str, df: pd.DataFrame) -> None:
        buffer = io.BytesIO()
        (df if not df.empty else pd.DataFrame()).to_parquet(
            buffer, index=False, compression="snappy"
        )
        buffer.seek(0)
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )

    def get_historial_row(self, historial_id: int) -> dict[str, Any] | None:
        self._ensure_historial_table()
        df = self.admin.read_table("sys_respaldos_historial")
        row = df[df["id"] == historial_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def delete_history(self, historial_id: int, *, remove_minio: bool = True) -> dict[str, Any]:
        """Elimina un registro del historial y, si aplica, los archivos en MinIO."""
        row = self.get_historial_row(historial_id)
        if not row:
            raise ValueError("Registro de historial no encontrado")
        estado = str(row.get("estado", "")).lower()
        if estado == "en_progreso":
            raise ValueError("No se puede eliminar un respaldo en ejecución")

        minio_deleted = 0
        if remove_minio:
            prefix = str(row.get("destino", "")).strip()
            if prefix:
                minio_deleted = self._delete_prefix(prefix)

        if not self.admin.delete_row("sys_respaldos_historial", historial_id):
            raise ValueError("No se pudo eliminar el registro del historial")

        return {
            "id": historial_id,
            "minio_objects_deleted": minio_deleted,
            "message": "Registro de respaldo eliminado",
        }

    def delete_history_bulk(self, ids: list[int]) -> dict[str, Any]:
        deleted: list[int] = []
        errors: list[dict[str, Any]] = []
        for raw_id in ids:
            try:
                hid = int(raw_id)
            except (TypeError, ValueError):
                errors.append({"id": raw_id, "error": "ID inválido"})
                continue
            try:
                self.delete_history(hid)
                deleted.append(hid)
            except Exception as exc:
                errors.append({"id": hid, "error": str(exc)})
        return {
            "deleted": deleted,
            "deleted_count": len(deleted),
            "errors": errors,
            "message": f"Eliminados {len(deleted)} registro(s) del historial",
        }

    def build_download_zip(self, historial_id: int) -> tuple[bytes, str]:
        """Empaqueta un respaldo de MinIO como ZIP para descargar en la PC."""
        row = self.get_historial_row(historial_id)
        if not row:
            raise ValueError("Registro de historial no encontrado")
        if str(row.get("estado", "")).lower() != "completado":
            raise ValueError("Solo se pueden descargar respaldos completados")

        prefix = str(row.get("destino", "")).strip()
        if not prefix:
            raise ValueError("Este respaldo no tiene ruta de destino en MinIO")

        buffer = io.BytesIO()
        count = 0
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for key in self._list_prefix(prefix):
                name = key[len(prefix) :] if key.startswith(prefix) else key
                if not name or name.endswith("/"):
                    continue
                body = self._s3.get_object(Bucket=self._bucket, Key=key)["Body"].read()
                zf.writestr(name.replace("\\", "/"), body)
                count += 1
            if count == 0:
                raise ValueError("No hay archivos en MinIO para este respaldo")

        ts = str(row.get("iniciado_en", "respaldo"))[:10].replace("-", "")
        nombre = row.get("nombre_config", "crimetrack").replace(" ", "_")
        filename = f"crimetrack_respaldo_{nombre}_{historial_id}_{ts}.zip"
        return buffer.getvalue(), filename

    def restore_from_zip(
        self,
        zip_bytes: bytes,
        *,
        ejecutado_por: str | None = None,
    ) -> dict[str, Any]:
        """
        Restaura tablas transaccionales y de administración desde un ZIP descargado.
        No restaura fact_crimes/dim_* (se regeneran con ETL).
        """
        restored_tx: list[str] = []
        restored_admin: list[str] = []
        errors: list[str] = []

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            names = zf.namelist()
            manifest = None
            if MANIFEST_NAME in names:
                manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))

            tx_tables = set(FULL_TABLES)
            admin_tables = set(ADMIN_TABLES)

            for name in names:
                if not name.endswith(".parquet"):
                    continue
                base = name.replace("\\", "/").split("/")[-1].replace(".parquet", "")
                try:
                    df = pd.read_parquet(io.BytesIO(zf.read(name)))
                except Exception as exc:
                    errors.append(f"{name}: {exc}")
                    continue

                if base in tx_tables:
                    try:
                        self.tx.write_table(base, df)
                        if base not in restored_tx:
                            restored_tx.append(base)
                    except Exception as exc:
                        errors.append(f"tx/{base}: {exc}")
                elif base in admin_tables:
                    try:
                        self.admin.write_table(base, df)
                        if base not in restored_admin:
                            restored_admin.append(base)
                    except Exception as exc:
                        errors.append(f"admin/{base}: {exc}")
                else:
                    errors.append(f"Tabla desconocida en ZIP: {base}")

        try:
            self.tx.append_row(
                "app_audit_logs",
                {
                    "fk_usuario": None,
                    "accion": "BACKUP_RESTORE",
                    "tabla_afectada": "minio_transaccional+admin",
                    "detalle": (
                        f"Restauración ZIP por {ejecutado_por or 'admin'}: "
                        f"tx={len(restored_tx)}, admin={len(restored_admin)}"
                    ),
                    "direccion_ip": "local",
                    "fecha_hora": utc_now_iso(),
                },
            )
        except Exception:
            pass

        ok = (restored_tx or restored_admin) and not errors
        return {
            "success": bool(restored_tx or restored_admin),
            "restored_transaccional": restored_tx,
            "restored_administracion": restored_admin,
            "errors": errors,
            "manifest": manifest,
            "etl_siguiente_paso": ETL_HINT,
            "message": (
                "Restauración completada. Ejecuta ETL para regenerar el modelo estrella."
                if ok
                else "Restauración parcial o fallida."
            ),
        }

    def _list_prefix(self, prefix: str) -> list[str]:
        keys: list[str] = []
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys

    def _delete_prefix(self, prefix: str) -> int:
        keys = self._list_prefix(prefix)
        if not keys:
            return 0
        for i in range(0, len(keys), 1000):
            batch = [{"Key": k} for k in keys[i : i + 1000]]
            self._s3.delete_objects(Bucket=self._bucket, Delete={"Objects": batch})
        return len(keys)

    def _notify_backup_failure(self, cfg: dict, detalle: str) -> None:
        from packages.autenticacion_seguridad.services.email_service import (
            send_backup_failure_alert,
        )

        try:
            df = self.tx.read_table("app_usuarios")
            comisarios = df[
                df["fk_rol"].astype(int) == 2
            ] if "fk_rol" in df.columns else pd.DataFrame()
            for _, u in comisarios.iterrows():
                email = str(u.get("email", "")).strip()
                if email:
                    send_backup_failure_alert(
                        to_email=email,
                        nombre=f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip(),
                        config_nombre=str(cfg.get("nombre", "Respaldo")),
                        detalle=detalle,
                    )
        except Exception:
            pass

        try:
            self.tx.append_row(
                "app_audit_logs",
                {
                    "fk_usuario": None,
                    "accion": "BACKUP_FAILED",
                    "tabla_afectada": "sys_respaldos_config",
                    "detalle": f"{cfg.get('nombre')}: {detalle}",
                    "direccion_ip": "sistema",
                    "fecha_hora": utc_now_iso(),
                },
            )
        except Exception:
            pass

    @staticmethod
    def _calc_next_run(
        frecuencia: str,
        hora: str,
        *,
        from_dt: datetime | None = None,
    ) -> str:
        base = from_dt or now_dt()
        hours = FREQ_HOURS.get(frecuencia.lower(), 24)
        nxt = base + timedelta(hours=hours)
        try:
            hh, mm = hora.split(":")[:2]
            nxt = nxt.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        except (ValueError, TypeError):
            pass
        return nxt.isoformat()

    @staticmethod
    def _is_due(cfg: dict, now: datetime) -> bool:
        """True solo si llegó la hora programada (no en cada visita a la pantalla)."""
        if not cfg.get("activo"):
            return False
        prox = str(cfg.get("proxima_ejecucion") or "").strip()
        if prox:
            try:
                dt = datetime.fromisoformat(prox.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return now >= dt
            except ValueError:
                pass
        ultima = str(cfg.get("ultima_ejecucion") or "").strip()
        if not ultima:
            return False
        try:
            last = datetime.fromisoformat(ultima.replace("Z", "+00:00"))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
        except ValueError:
            return False
        hours = FREQ_HOURS.get(str(cfg.get("frecuencia", "diario")).lower(), 24)
        return now >= last + timedelta(hours=hours)


def now_dt() -> datetime:
    return datetime.now(timezone.utc)
