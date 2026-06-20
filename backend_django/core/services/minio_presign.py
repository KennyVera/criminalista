"""
URLs firmadas de lectura MinIO — Direct-to-Client (bypass Django JSON).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from core.services.minio_store import MinioParquetStore


class MinioPresignService:
    def __init__(self, store: MinioParquetStore | None = None) -> None:
        self.store = store or MinioParquetStore()
        self.default_ttl = int(os.getenv("MINIO_PRESIGN_TTL_SECONDS", "3600"))

    def presign_get(self, key: str, *, expires_in: int | None = None) -> str:
        ttl = expires_in if expires_in is not None else self.default_ttl
        return self.store._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.store.bucket, "Key": key},
            ExpiresIn=max(60, min(ttl, 86_400)),
        )

    def presign_parquet_artifact(
        self,
        key: str,
        *,
        artifact_id: str,
        label: str,
        expires_in: int | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        ttl = expires_in if expires_in is not None else self.default_ttl
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        return {
            "id": artifact_id,
            "label": label,
            "format": "parquet",
            "compression": "snappy",
            "key": key,
            "url": self.presign_get(key, expires_in=ttl),
            "expires_in": ttl,
            "expires_at": expires_at.isoformat(),
            "columns": columns or [],
        }

    def star_artifact_keys(self) -> dict[str, str]:
        keys: dict[str, str] = {}
        if self.store.has_consolidated_facts():
            keys["fact_crimes"] = self.store.fact_crimes_consolidated_key()
        elif self.store.has_partitioned_facts():
            keys["fact_crimes"] = self.store.fact_crimes_glob().replace(f"{self.store.bucket}/", "")
        else:
            keys["fact_crimes"] = self.store._object_key("fact_crimes")

        for dim in (
            "dim_distrito_policial",
            "dim_tipo_crimen",
            "dim_tiempo",
            "dim_caso",
        ):
            keys[dim] = self.store._object_key(dim)
        return keys

    def build_analytics_manifest(self, *, expires_in: int | None = None) -> dict[str, Any]:
        ttl = expires_in if expires_in is not None else self.default_ttl
        keys = self.star_artifact_keys()
        column_hints: dict[str, list[str]] = {
            "fact_crimes": [
                "id",
                "fk_caso",
                "fk_distrito",
                "fk_tipo_crimen",
                "fk_tiempo",
            ],
            "dim_distrito_policial": ["id", "district", "beat"],
            "dim_tipo_crimen": ["id", "primary_type", "description"],
            "dim_tiempo": ["id", "year", "month", "date"],
            "dim_caso": ["id", "case_number", "estado_caso", "prioridad_caso"],
        }
        artifacts = [
            self.presign_parquet_artifact(
                key,
                artifact_id=artifact_id,
                label=artifact_id,
                expires_in=ttl,
                columns=column_hints.get(artifact_id, []),
            )
            for artifact_id, key in keys.items()
        ]
        return {
            "strategy": "direct_to_client",
            "bucket": self.store.bucket,
            "expires_in": ttl,
            "artifacts": artifacts,
            "query_templates": {
                "filtered_aggregate": """
SELECT
  CAST(d.district AS VARCHAR) AS distrito,
  CAST(t.primary_type AS VARCHAR) AS tipo,
  CAST(ti.year AS VARCHAR) AS anio,
  COUNT(*)::BIGINT AS total
FROM read_parquet('{{fact_crimes}}') AS f
INNER JOIN read_parquet('{{dim_distrito_policial}}') AS d
  ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
INNER JOIN read_parquet('{{dim_tipo_crimen}}') AS t
  ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(t.id AS BIGINT)
INNER JOIN read_parquet('{{dim_tiempo}}') AS ti
  ON CAST(f.fk_tiempo AS BIGINT) = CAST(ti.id AS BIGINT)
GROUP BY d.district, t.primary_type, ti.year
ORDER BY total DESC
LIMIT 500
""".strip(),
            },
        }
