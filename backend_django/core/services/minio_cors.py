"""
Configuración CORS del bucket MinIO — necesario para Presigned URLs en el navegador.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Any

from django.conf import settings

from core.services.minio_store import MinioParquetStore


def default_cors_origins() -> list[str]:
    env_raw = os.getenv("MINIO_CORS_ORIGINS", "").strip()
    if env_raw:
        return [o.strip() for o in env_raw.split(",") if o.strip()]
    origins = list(getattr(settings, "CORS_ALLOWED_ORIGINS", []) or [])
    extras = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    seen: set[str] = set()
    out: list[str] = []
    for origin in [*origins, *extras]:
        if origin and origin not in seen:
            seen.add(origin)
            out.append(origin)
    return out


class MinioCorsService:
    def __init__(self, store: MinioParquetStore | None = None) -> None:
        self.store = store or MinioParquetStore()
        self.bucket = self.store.bucket
        self._client = self.store._client

    def get_current_cors(self) -> dict[str, Any] | None:
        try:
            resp = self._client.get_bucket_cors(Bucket=self.bucket)
            return resp.get("CORSRules", resp)
        except self._client.exceptions.ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchCORSConfiguration", "NoSuchBucket"):
                return None
            raise

    def build_cors_configuration(
        self,
        *,
        origins: list[str] | None = None,
        methods: list[str] | None = None,
        max_age: int = 3600,
    ) -> dict[str, Any]:
        allowed_origins = origins or default_cors_origins()
        if not allowed_origins:
            raise ValueError("Se requiere al menos un origen CORS.")

        allowed_methods = methods or ["GET", "HEAD", "PUT", "POST", "DELETE"]
        return {
            "CORSRules": [
                {
                    "AllowedOrigins": allowed_origins,
                    "AllowedMethods": allowed_methods,
                    "AllowedHeaders": ["*"],
                    "ExposeHeaders": ["ETag", "Content-Length"],
                    "MaxAgeSeconds": int(max_age),
                }
            ]
        }

    def _apply_via_boto3(self, config: dict[str, Any]) -> None:
        self._client.put_bucket_cors(Bucket=self.bucket, CORSConfiguration=config)

    def _ensure_mc_alias(self, container: str, alias: str) -> None:
        access = os.getenv("MINIO_ROOT_USER", "minioadmin")
        secret = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_change_me")
        endpoint = os.getenv("MINIO_INTERNAL_ENDPOINT", "http://localhost:9000")
        subprocess.run(
            [
                "docker",
                "exec",
                container,
                "mc",
                "alias",
                "set",
                alias,
                endpoint,
                access,
                secret,
                "--api",
                "S3v4",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def _build_cors_xml(self, config: dict[str, Any]) -> str:
        rules = config.get("CORSRules") or []
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">',
        ]
        for rule in rules:
            parts.append("  <CORSRule>")
            for origin in rule.get("AllowedOrigins") or []:
                parts.append(f"    <AllowedOrigin>{origin}</AllowedOrigin>")
            for method in rule.get("AllowedMethods") or []:
                parts.append(f"    <AllowedMethod>{method}</AllowedMethod>")
            for header in rule.get("AllowedHeaders") or ["*"]:
                parts.append(f"    <AllowedHeader>{header}</AllowedHeader>")
            for expose in rule.get("ExposeHeaders") or []:
                parts.append(f"    <ExposeHeader>{expose}</ExposeHeader>")
            max_age = int(rule.get("MaxAgeSeconds") or 3600)
            parts.append(f"    <MaxAgeSeconds>{max_age}</MaxAgeSeconds>")
            parts.append("  </CORSRule>")
        parts.append("</CORSConfiguration>")
        return "\n".join(parts)

    def _apply_via_mc_bucket(self, config: dict[str, Any]) -> dict[str, Any]:
        container = os.getenv("MINIO_DOCKER_CONTAINER", "crimetrack-minio")
        alias = os.getenv("MINIO_MC_ALIAS", "crimetrack")
        self._ensure_mc_alias(container, alias)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".xml",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(self._build_cors_xml(config))
            host_path = tmp.name

        container_path = "/tmp/crimetrack_cors.xml"
        subprocess.run(
            ["docker", "cp", host_path, f"{container}:{container_path}"],
            check=True,
            capture_output=True,
            text=True,
        )
        try:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    container,
                    "mc",
                    "cors",
                    "set",
                    f"{alias}/{self.bucket}",
                    container_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            try:
                os.remove(host_path)
            except OSError:
                pass
            subprocess.run(
                ["docker", "exec", container, "rm", "-f", container_path],
                capture_output=True,
                text=True,
            )
        return {"method": "mc_bucket_cors", "container": container, "alias": alias}

    def _apply_via_mc_admin_api(self, origins: list[str]) -> dict[str, Any]:
        container = os.getenv("MINIO_DOCKER_CONTAINER", "crimetrack-minio")
        alias = os.getenv("MINIO_MC_ALIAS", "crimetrack")
        self._ensure_mc_alias(container, alias)

        origin_csv = ",".join(origins)
        subprocess.run(
            [
                "docker",
                "exec",
                container,
                "mc",
                "admin",
                "config",
                "set",
                alias,
                "api",
                f"cors_allow_origin={origin_csv}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["docker", "restart", container],
            check=True,
            capture_output=True,
            text=True,
        )
        return {
            "method": "mc_admin_api",
            "container": container,
            "alias": alias,
            "cors_allow_origin": origin_csv,
        }

    def _apply_via_mc(self, config: dict[str, Any], *, origins: list[str]) -> dict[str, Any]:
        try:
            return self._apply_via_mc_bucket(config)
        except Exception:
            return self._apply_via_mc_admin_api(origins)

    def apply_cors(
        self,
        *,
        origins: list[str] | None = None,
        methods: list[str] | None = None,
        max_age: int = 3600,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        config = self.build_cors_configuration(
            origins=origins,
            methods=methods,
            max_age=max_age,
        )
        previous = self.get_current_cors()

        if dry_run:
            return {
                "dry_run": True,
                "bucket": self.bucket,
                "endpoint": self.store.endpoint,
                "applied": False,
                "configuration": config,
                "previous": previous,
            }

        allowed_origins = (config.get("CORSRules") or [{}])[0].get("AllowedOrigins") or []
        apply_method = "boto3"
        mc_meta: dict[str, Any] = {}
        try:
            self._apply_via_boto3(config)
        except Exception as boto_exc:
            try:
                mc_meta = self._apply_via_mc(config, origins=allowed_origins)
                apply_method = str(mc_meta.get("method", "mc_docker"))
            except Exception as mc_exc:
                raise RuntimeError(
                    f"boto3 PutBucketCors falló ({boto_exc}); "
                    f"fallback mc también falló ({mc_exc})"
                ) from mc_exc

        return {
            "dry_run": False,
            "bucket": self.bucket,
            "endpoint": self.store.endpoint,
            "applied": True,
            "apply_method": apply_method,
            "mc": mc_meta,
            "configuration": config,
            "previous": previous,
        }

    @staticmethod
    def format_report(result: dict[str, Any]) -> str:
        lines = [
            f"Bucket: {result['bucket']}",
            f"Endpoint: {result['endpoint']}",
            f"Aplicado: {'sí' if result.get('applied') else 'no (dry-run)'}",
            "Reglas CORS:",
            json.dumps(result.get("configuration"), indent=2, ensure_ascii=False),
        ]
        if result.get("apply_method"):
            lines.append(f"Método: {result['apply_method']}")
        if result.get("mc"):
            lines.append(f"Detalle MC: {json.dumps(result['mc'], ensure_ascii=False)}")
        if result.get("previous"):
            lines.extend(["", "Configuración anterior:", json.dumps(result["previous"], indent=2)])
        return "\n".join(lines)
