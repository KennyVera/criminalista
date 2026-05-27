from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from packages.administracion_sistema.storage import AdminMinioStore
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso


class BackupsAdminService:
    def __init__(self) -> None:
        self.admin = AdminMinioStore()
        self.tx = TransactionalMinioStore()

    def get_config(self) -> list[dict]:
        return self.admin.read_table("sys_respaldos_config").to_dict(orient="records")

    def update_config(self, config_id: int, data: dict) -> dict | None:
        return self.admin.update_row("sys_respaldos_config", config_id, data)

    def run_backup(self, config_id: int = 1) -> dict[str, Any]:
        cfg = self.admin.read_table("sys_respaldos_config")
        row = cfg[cfg["id"] == config_id]
        if row.empty:
            raise ValueError("Configuración de respaldo no encontrada")
        c = row.iloc[0]
        prefix = str(c["destino_minio_prefix"])
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = f"{prefix}/{ts}/"
        copied = 0

        for table in [
            "app_roles",
            "app_usuarios",
            "app_sesiones_activas",
            "app_audit_logs",
        ]:
            try:
                df = self.tx.read_table(table)
                if not df.empty:
                    buffer = io.BytesIO()
                    df.to_parquet(buffer, index=False, compression="snappy")
                    buffer.seek(0)
                    key = f"{dest}{table}.parquet"
                    self.tx._client.put_object(
                        Bucket=self.tx.bucket,
                        Key=key,
                        Body=buffer.getvalue(),
                        ContentType="application/octet-stream",
                    )
                    copied += 1
            except Exception:
                pass

        self.admin.update_row(
            "sys_respaldos_config",
            config_id,
            {
                "ultima_ejecucion": utc_now_iso(),
                "ultimo_estado": f"OK — {copied} tablas copiadas a {dest}",
            },
        )
        return {
            "success": True,
            "destino": dest,
            "tablas_copiadas": copied,
            "timestamp": ts,
        }
