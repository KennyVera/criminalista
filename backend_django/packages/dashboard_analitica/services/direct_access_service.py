"""
Direct-to-Client: manifest ligero con Presigned URLs (sin serializar OLAP en Django).
"""

from __future__ import annotations

from typing import Any

from django.core.cache import cache

from core.cache.invalidation import DIRECT_MANIFEST_KEY
from core.services.duckdb_s3 import DuckDBS3Session
from core.services.minio_presign import MinioPresignService

MANIFEST_CACHE_TTL = 300


class DashboardDirectAccessService:
    def __init__(self) -> None:
        self.presign = MinioPresignService()
        self.duckdb = DuckDBS3Session.shared()

    def manifest(self, *, expires_in: int | None = None) -> dict[str, Any]:
        gen = cache.get("crimetrack:cache:generation") or 1
        cache_key = f"{DIRECT_MANIFEST_KEY}:g{gen}"
        cached = cache.get(cache_key)
        if cached:
            return {**cached, "_from_cache": True}

        payload = self.presign.build_analytics_manifest(expires_in=expires_in)
        payload["cache_generation"] = int(gen)
        cache.set(cache_key, payload, MANIFEST_CACHE_TTL)
        return payload

    def presign_artifact(self, artifact_id: str, *, expires_in: int | None = None) -> dict[str, Any]:
        keys = self.presign.star_artifact_keys()
        key = keys.get(artifact_id)
        if not key or "*" in key:
            raise ValueError(f"Artefacto no disponible para presign: {artifact_id}")
        return self.presign.presign_parquet_artifact(
            key,
            artifact_id=artifact_id,
            label=artifact_id,
            expires_in=expires_in,
        )

    def server_side_preview(
        self,
        *,
        distrito: str | None = None,
        tipo: str | None = None,
        year: str | None = None,
        month: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """
        Vista previa agregada ejecutada en DuckDB servidor (pocas filas).
        Para tablas masivas el cliente debe usar manifest + DuckDB-Wasm.
        """
        return self.duckdb.filtered_crimes_aggregate(
            distrito=distrito,
            tipo=tipo,
            year=year,
            month=month,
            limit=limit,
        )
