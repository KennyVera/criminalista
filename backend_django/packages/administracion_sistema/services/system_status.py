from __future__ import annotations

import os
from typing import Any

from django.conf import settings
from django.core.cache import cache

from core.services.minio_store import MinioParquetStore
from core.services.pocketbase import PocketBaseClient
from packages.administracion_sistema.storage import AdminMinioStore
from packages.shared.minio_transactional import TransactionalMinioStore


class SystemStatusService:
    def supervise(self) -> dict[str, Any]:
        components = []

        pb_ok = False
        try:
            pb_ok = PocketBaseClient().health()
        except Exception as exc:
            pb_err = str(exc)
        else:
            pb_err = None
        components.append(
            {
                "nombre": "PocketBase",
                "estado": "operativo" if pb_ok else "caido",
                "detalle": settings.POCKETBASE_URL,
                "error": pb_err,
            }
        )

        minio_ok = False
        minio_err = None
        try:
            store = MinioParquetStore()
            store._client.head_bucket(Bucket=store.bucket)
            minio_ok = True
        except Exception as exc:
            minio_err = str(exc)
        components.append(
            {
                "nombre": "MinIO",
                "estado": "operativo" if minio_ok else "caido",
                "detalle": settings.MINIO_ENDPOINT,
                "error": minio_err,
            }
        )

        redis_ok = False
        redis_err = None
        try:
            cache.set("crimetrack:health:ping", "1", 10)
            redis_ok = cache.get("crimetrack:health:ping") == "1"
        except Exception as exc:
            redis_err = str(exc)
        components.append(
            {
                "nombre": "Redis",
                "estado": "operativo" if redis_ok else "caido",
                "detalle": os.getenv("REDIS_CACHE_URL", ""),
                "error": redis_err,
            }
        )

        components.append(
            {
                "nombre": "Django API",
                "estado": "operativo",
                "detalle": "REST API CrimeTrack",
                "error": None,
            }
        )

        from packages.shared.minio_transactional import utc_now_iso

        tx = TransactionalMinioStore()
        admin = AdminMinioStore()
        ses = tx.read_table("app_sesiones_activas")
        if not ses.empty:
            active_mask = ses["activa"].astype(str).str.lower().isin(("true", "1", "1.0"))
            sesiones = int(active_mask.sum())
        else:
            sesiones = 0

        datasets = {
            "usuarios": len(tx.read_table("app_usuarios")),
            "sesiones_activas": sesiones,
            "catalogos_delitos": len(admin.read_table("sys_catalogo_delitos")),
            "zonas_geograficas": len(admin.read_table("sys_zonas_geograficas")),
        }

        all_ok = all(c["estado"] == "operativo" for c in components)
        return {
            "estado_general": "saludable" if all_ok else "degradado",
            "componentes": components,
            "datasets": datasets,
            "timestamp": utc_now_iso(),
        }
