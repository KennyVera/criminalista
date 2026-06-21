"""
Servicio del paquete Gestión de Evidencias Digitales (P06).

Implementa:
- CU-O27/O28: carga de evidencia a MinIO con cálculo de hash SHA-256 (integridad).
- CU-O29: gestión de la cadena de custodia con transiciones de estado validadas y auditadas.
- CU-O30: consulta de evidencias autorizadas por expediente.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore
from packages.expedientes_criminales.services.datalake_service import ExpedienteDatalakeService
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

ESTADO_INICIAL = "En custodia"

# Cadena de custodia: estados válidos y transiciones permitidas (CU-O29).
ESTADOS_CUSTODIA = (
    "En custodia",
    "En análisis",
    "Transferida",
    "Liberada",
    "Destruida",
)

TRANSICIONES: dict[str, tuple[str, ...]] = {
    "En custodia": ("En análisis", "Transferida", "Liberada", "Destruida"),
    "En análisis": ("En custodia", "Transferida", "Liberada"),
    "Transferida": ("En custodia", "En análisis"),
    "Liberada": ("En custodia",),
    "Destruida": (),  # estado terminal
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


class EvidenciasService:
    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()
        self.datalake = ExpedienteDatalakeService()
        self.olap = MinioParquetStore()
        self.tx.ensure_tables()
        self._bucket = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
        self._prefix = os.getenv("MINIO_EVIDENCE_PREFIX", "evidencias")

    # ── Lectura ──
    def list_by_case(self, case_number: str) -> list[dict[str, Any]]:
        fk_caso = self.datalake.resolve_fk_caso(case_number)
        if not fk_caso:
            return []
        df = self.tx.read_table("app_evidencias")
        if df.empty:
            return []
        mask = df["fk_caso"].astype(int) == int(fk_caso)
        rows = df[mask].sort_values("fecha_subida", ascending=False)
        return [_json_safe(r) for r in rows.to_dict(orient="records")]

    def get(self, id_evidencia: int) -> dict[str, Any] | None:
        df = self.tx.read_table("app_evidencias")
        if df.empty:
            return None
        mask = df["id_evidencia"].astype(int) == int(id_evidencia)
        if not mask.any():
            return None
        return _json_safe(df[mask].iloc[0].to_dict())

    # ── Carga con hash (CU-O27/O28) ──
    @staticmethod
    def compute_sha256(body: bytes) -> str:
        return hashlib.sha256(body).hexdigest()

    def upload(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        file_obj: Any,
        filename: str,
        tipo_evidencia: str = "Multimedia",
    ) -> dict[str, Any]:
        fk_caso = self.datalake.resolve_fk_caso(case_number)
        if not fk_caso:
            raise ValueError("Caso no encontrado")

        body = file_obj.read()
        hash_sha256 = self.compute_sha256(body)
        size_mb = round(len(body) / (1024 * 1024), 3)

        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-") or "archivo"
        key = f"{self._prefix}/{case_number}/{uuid.uuid4().hex}_{safe_name}"
        self.olap._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=getattr(file_obj, "content_type", None) or "application/octet-stream",
        )

        now = utc_now_iso()
        row = {
            "fk_caso": int(fk_caso),
            "fk_usuario_carga": int(user["id_usuario"]),
            "tipo_evidencia": tipo_evidencia,
            "nombre_archivo": filename,
            "minio_url": f"s3://{self._bucket}/{key}",
            "peso_mb": size_mb,
            "hash_sha256": hash_sha256,
            "algoritmo_hash": "SHA-256",
            "estado_custodia": ESTADO_INICIAL,
            "fecha_subida": now,
            "fecha_actualizacion_custodia": now,
            "fk_usuario_custodia": int(user["id_usuario"]),
        }
        return _json_safe(self.tx.append_row("app_evidencias", row))

    # ── Cadena de custodia (CU-O29) ──
    @staticmethod
    def next_states(estado_actual: str) -> list[str]:
        return list(TRANSICIONES.get(str(estado_actual), ()))

    def change_custody(
        self,
        id_evidencia: int,
        *,
        nuevo_estado: str,
        user: dict[str, Any],
        motivo: str = "",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Cambia el estado de custodia validando la transición. Devuelve (antes, despues)."""
        nuevo_estado = str(nuevo_estado).strip()
        if nuevo_estado not in ESTADOS_CUSTODIA:
            raise ValueError(
                f"Estado de custodia inválido. Use uno de: {', '.join(ESTADOS_CUSTODIA)}"
            )

        df = self.tx.read_table("app_evidencias")
        if df.empty:
            raise ValueError("Evidencia no encontrada")
        mask = df["id_evidencia"].astype(int) == int(id_evidencia)
        if not mask.any():
            raise ValueError("Evidencia no encontrada")

        antes = _json_safe(df[mask].iloc[0].to_dict())
        actual = str(antes.get("estado_custodia") or ESTADO_INICIAL)

        if nuevo_estado == actual:
            raise ValueError(f"La evidencia ya está en estado «{actual}»")
        permitidos = TRANSICIONES.get(actual, ())
        if nuevo_estado not in permitidos:
            raise ValueError(
                f"Transición no permitida: «{actual}» → «{nuevo_estado}». "
                f"Permitidas: {', '.join(permitidos) or 'ninguna (estado terminal)'}"
            )

        now = utc_now_iso()
        df.loc[mask, "estado_custodia"] = nuevo_estado
        df.loc[mask, "fecha_actualizacion_custodia"] = now
        df.loc[mask, "fk_usuario_custodia"] = int(user["id_usuario"])
        self.tx.write_table("app_evidencias", df)

        despues = _json_safe(df[mask].iloc[0].to_dict())
        if motivo:
            antes = {**antes, "motivo_cambio": motivo}
            despues = {**despues, "motivo_cambio": motivo}
        return antes, despues
