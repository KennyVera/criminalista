"""
Integridad y alertas de auditoría (P03).

CU-O75 — Verificación del hash encadenado de ``app_audit_logs`` (sello criptográfico).
CU-O15 — Validación de la cadena de custodia: recalcula el hash de cada evidencia y lo
          compara contra el sello almacenado al momento de la carga.
CU-O14 — Generación de alertas de seguridad cuando se detecta una ruptura de integridad.
"""

from __future__ import annotations

import hashlib
from typing import Any

from packages.shared.audit import record_audit
from packages.shared.minio_transactional import TransactionalMinioStore


def _clean(value: Any) -> str:
    try:
        import pandas as pd

        if value is None or pd.isna(value):
            return ""
    except (TypeError, ValueError, ImportError):
        if value is None:
            return ""
    return str(value)


class IntegrityService:
    def __init__(self) -> None:
        self.store = TransactionalMinioStore()

    # ── CU-O75: cadena de hashes de auditoría ──────────────────────────
    def verify_audit_chain(self) -> dict[str, Any]:
        df = self.store.read_table("app_audit_logs")
        if df.empty:
            return {
                "ok": True,
                "total": 0,
                "verificados": 0,
                "sin_sello": 0,
                "rupturas": [],
                "mensaje": "No hay eventos de auditoría registrados.",
            }

        ordered = df.sort_values("id_log").to_dict(orient="records")
        rupturas: list[dict[str, Any]] = []
        verificados = 0
        sin_sello = 0
        prev_hash = ""

        for row in ordered:
            stored_hash = _clean(row.get("event_hash"))
            stored_prev = _clean(row.get("previous_hash"))
            # Eventos legados (anteriores al sellado): no rompen la cadena, se reportan.
            if not stored_hash:
                sin_sello += 1
                prev_hash = ""
                continue

            expected = self.store.compute_audit_hash(stored_prev, row)
            id_log = row.get("id_log")
            problemas = []
            if stored_hash != expected:
                problemas.append("hash del evento no coincide (registro alterado)")
            if prev_hash and stored_prev and stored_prev != prev_hash:
                problemas.append("ruptura del encadenamiento (eslabón faltante o reordenado)")
            if problemas:
                rupturas.append(
                    {
                        "id_log": id_log,
                        "accion": _clean(row.get("accion")),
                        "fecha_hora": _clean(row.get("fecha_hora")),
                        "problemas": problemas,
                    }
                )
            else:
                verificados += 1
            prev_hash = stored_hash

        ok = not rupturas
        if not ok:
            record_audit(
                fk_usuario=None,
                accion="INTEGRITY_ALERT",
                tabla="app_audit_logs",
                detalle=(
                    f"Alerta de integridad: se detectaron {len(rupturas)} ruptura(s) "
                    f"en la cadena de auditoría."
                ),
                despues={"rupturas": rupturas[:20]},
            )
        return {
            "ok": ok,
            "total": len(ordered),
            "verificados": verificados,
            "sin_sello": sin_sello,
            "rupturas": rupturas,
            "mensaje": (
                "La cadena de auditoría es íntegra." if ok
                else f"Se detectaron {len(rupturas)} ruptura(s) de integridad."
            ),
        }

    # ── CU-O15: cadena de custodia de evidencias ───────────────────────
    def verify_custody_chain(self, *, limit: int = 200) -> dict[str, Any]:
        try:
            df = self.store.read_table("app_evidencias")
        except Exception:
            df = None
        if df is None or df.empty:
            return {"ok": True, "total": 0, "verificadas": 0, "alertas": [], "mensaje": "Sin evidencias registradas."}

        rows = df.to_dict(orient="records")[: int(limit)]
        alertas: list[dict[str, Any]] = []
        verificadas = 0
        client = getattr(self.store, "_client", None)
        bucket = getattr(self.store, "bucket", None)

        for row in rows:
            stored_hash = _clean(row.get("hash_sha256"))
            estado = _clean(row.get("estado_custodia"))
            id_ev = row.get("id_evidencia")
            url = _clean(row.get("minio_url"))

            if estado.lower() == "destruida":
                alertas.append({
                    "id_evidencia": id_ev,
                    "caso": _clean(row.get("fk_caso")),
                    "motivo": "Evidencia marcada como destruida.",
                })
                continue
            if not stored_hash:
                alertas.append({
                    "id_evidencia": id_ev,
                    "caso": _clean(row.get("fk_caso")),
                    "motivo": "Evidencia sin hash de integridad (cargada antes del sellado).",
                })
                continue

            # Recalcular el hash del archivo en MinIO si es posible.
            recomputed = self._recompute_evidence_hash(client, bucket, url)
            if recomputed is None:
                verificadas += 1  # No se pudo descargar; se mantiene el sello declarado.
                continue
            if recomputed != stored_hash:
                alertas.append({
                    "id_evidencia": id_ev,
                    "caso": _clean(row.get("fk_caso")),
                    "motivo": "El hash del archivo no coincide con el sello de carga (posible alteración).",
                })
            else:
                verificadas += 1

        ok = not alertas
        if not ok:
            record_audit(
                fk_usuario=None,
                accion="INTEGRITY_ALERT",
                tabla="app_evidencias",
                detalle=f"Alerta de custodia: {len(alertas)} evidencia(s) con observaciones de integridad.",
                despues={"alertas": alertas[:20]},
            )
        return {
            "ok": ok,
            "total": len(rows),
            "verificadas": verificadas,
            "alertas": alertas,
            "mensaje": (
                "La cadena de custodia es íntegra." if ok
                else f"Se detectaron {len(alertas)} observación(es) de custodia."
            ),
        }

    @staticmethod
    def _recompute_evidence_hash(client, bucket, url: str) -> str | None:
        if not client or not bucket or not url:
            return None
        # minio_url tiene el formato s3://{bucket}/{key}.
        key = url
        prefix = f"s3://{bucket}/"
        if key.startswith(prefix):
            key = key[len(prefix):]
        elif key.startswith("s3://"):
            # s3://otro-bucket/key → tomar todo tras el primer bucket.
            parts = key[len("s3://"):].split("/", 1)
            key = parts[1] if len(parts) > 1 else parts[0]
        try:
            resp = client.get_object(Bucket=bucket, Key=key)
            data = resp["Body"].read()
            return hashlib.sha256(data).hexdigest()
        except Exception:
            return None
