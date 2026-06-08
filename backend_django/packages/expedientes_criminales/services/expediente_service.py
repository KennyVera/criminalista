from __future__ import annotations

import io
import os
import uuid
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore
from packages.expedientes_criminales.services.datalake_service import ExpedienteDatalakeService
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

TIPOS_INVOLUCRADO = ("Víctima", "Testigo", "Sospechoso")
ESTADOS_CASO = ("Abierto", "En investigación", "Resuelto", "Cerrado", "Archivado")


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
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


def _avance_por_estado(estado: str) -> int:
    mapping = {
        "abierto": 15,
        "en investigación": 55,
        "cerrado": 90,
        "archivado": 100,
        "resuelto": 90,
        "importado": 15,
    }
    return mapping.get(str(estado or "").lower().strip(), 30)


class ExpedienteService:
    def __init__(self) -> None:
        self.tx = TransactionalMinioStore()
        self.datalake = ExpedienteDatalakeService()
        self.olap = MinioParquetStore()
        self.tx.ensure_tables()
        self._evidence_bucket = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
        self._evidence_prefix = os.getenv("MINIO_EVIDENCE_PREFIX", "evidencias")

    def _normalize_case(self, case_number: str) -> str:
        return str(case_number).strip()

    def detective_has_active_assignment(self, fk_detective: int, case_number: str) -> bool:
        cn = self._normalize_case(case_number).upper()
        df = self.tx.read_table("app_asignaciones")
        if df.empty:
            return False
        mask = (
            (df["case_number"].astype(str).str.upper() == cn)
            & (df["fk_detective"].astype(int) == fk_detective)
            & (df["estado_asignacion"].astype(str) == "Activa")
        )
        return bool(mask.any())

    def get_cabecera(self, case_number: str) -> dict[str, Any]:
        cn = self._normalize_case(case_number)
        fk_caso = self.datalake.resolve_fk_caso(cn)
        dim = None
        if fk_caso:
            dim = self.olap.get_record("dim_caso", str(fk_caso))

        asig_df = self.tx.read_table("app_asignaciones")
        asig = None
        if not asig_df.empty:
            mask = (
                asig_df["case_number"].astype(str).str.upper() == cn.upper()
            ) & (asig_df["estado_asignacion"].astype(str) == "Activa")
            if mask.any():
                asig = asig_df[mask].iloc[0].to_dict()

        bitacora = self._latest_bitacora(cn)
        if bitacora:
            avance = _safe_int(bitacora.get("avance_pct"))
            estado_caso = bitacora.get("estado_caso")
        elif asig:
            avance_raw = asig.get("avance_pct_actual")
            if pd.isna(avance_raw):
                estado_snap = str(
                    asig.get("estado_caso_snapshot") or (dim or {}).get("estado_caso") or ""
                )
                avance = _avance_por_estado(estado_snap)
            else:
                avance = _safe_int(avance_raw)
            estado_caso = (
                asig.get("estado_caso_snapshot") or (dim or {}).get("estado_caso")
            )
        else:
            avance = 0
            estado_caso = (dim or {}).get("estado_caso")

        if asig:
            asig = _json_safe(asig)
        if dim:
            dim = _json_safe(dim)

        return {
            "case_number": cn,
            "fk_caso": fk_caso,
            "dim_caso": dim,
            "asignacion": asig,
            "avance_pct": avance,
            "estado_caso": estado_caso,
        }

    def detalles_generales(self, case_number: str) -> dict[str, Any]:
        return self.datalake.get_hechos_by_case_number(case_number)

    def list_involucrados(self, case_number: str) -> list[dict[str, Any]]:
        fk_caso = self.datalake.resolve_fk_caso(case_number)
        if not fk_caso:
            return []

        rel_df = self.tx.read_table("app_caso_involucrado")
        inv_df = self.tx.read_table("app_involucrados")
        if rel_df.empty or inv_df.empty:
            return []

        rels = rel_df[rel_df["fk_caso"].astype(int) == fk_caso]
        items = []
        for rel in rels.to_dict(orient="records"):
            inv = inv_df[inv_df["id_involucrado"].astype(int) == int(rel["fk_involucrado"])]
            if inv.empty:
                continue
            row = inv.iloc[0].to_dict()
            items.append(
                {
                    "id_relacion": int(rel["id_relacion"]),
                    "id_involucrado": int(row["id_involucrado"]),
                    "tipo_relacion": rel.get("tipo_relacion"),
                    "declaracion": rel.get("declaracion"),
                    "nombres": row.get("nombres"),
                    "apellidos": row.get("apellidos"),
                    "identificacion": row.get("identificacion"),
                    "fecha_nacimiento": row.get("fecha_nacimiento"),
                    "antecedentes": row.get("antecedentes"),
                }
            )
        return items

    def add_involucrado(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        fk_caso = self.datalake.resolve_fk_caso(case_number)
        if not fk_caso:
            raise ValueError("Caso no encontrado en dim_caso")

        tipo = str(data.get("tipo_relacion", "Testigo"))
        if tipo not in TIPOS_INVOLUCRADO:
            raise ValueError(f"tipo_relacion debe ser uno de: {TIPOS_INVOLUCRADO}")

        inv_row = {
            "identificacion": str(data.get("identificacion", "")).strip(),
            "nombres": str(data.get("nombres", "")).strip(),
            "apellidos": str(data.get("apellidos", "")).strip(),
            "fecha_nacimiento": data.get("fecha_nacimiento", ""),
            "antecedentes": str(data.get("antecedentes", "")).strip(),
        }
        created_inv = self.tx.append_row("app_involucrados", inv_row)
        rel_row = {
            "fk_caso": fk_caso,
            "fk_involucrado": int(created_inv["id_involucrado"]),
            "tipo_relacion": tipo,
            "declaracion": str(data.get("declaracion", "")).strip(),
            "fecha_asociacion": utc_now_iso(),
        }
        created_rel = self.tx.append_row("app_caso_involucrado", rel_row)
        return {**created_inv, **created_rel}

    def list_evidencias(self, case_number: str) -> list[dict[str, Any]]:
        fk_caso = self.datalake.resolve_fk_caso(case_number)
        if not fk_caso:
            return []
        df = self.tx.read_table("app_evidencias")
        if df.empty:
            return []
        mask = df["fk_caso"].astype(int) == fk_caso
        return [_json_safe(r) for r in df[mask].to_dict(orient="records")]

    def upload_evidencia(
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

        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-") or "archivo"
        key = f"{self._evidence_prefix}/{case_number}/{uuid.uuid4().hex}_{safe_name}"
        body = file_obj.read()
        size_mb = round(len(body) / (1024 * 1024), 3)

        self.olap._client.put_object(
            Bucket=self._evidence_bucket,
            Key=key,
            Body=body,
            ContentType=getattr(file_obj, "content_type", None) or "application/octet-stream",
        )

        minio_url = f"s3://{self._evidence_bucket}/{key}"
        row = {
            "fk_caso": fk_caso,
            "fk_usuario_carga": int(user["id_usuario"]),
            "tipo_evidencia": tipo_evidencia,
            "minio_url": minio_url,
            "peso_mb": size_mb,
            "estado_custodia": "En custodia",
            "fecha_subida": utc_now_iso(),
        }
        return self.tx.append_row("app_evidencias", row)

    def list_bitacora(self, case_number: str) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_expediente_bitacora")
        if df.empty:
            return []
        cn = self._normalize_case(case_number).upper()
        mask = df["case_number"].astype(str).str.upper() == cn
        items = df[mask].sort_values("fecha_hora", ascending=False)
        return [_json_safe(r) for r in items.to_dict(orient="records")]

    def _latest_bitacora(self, case_number: str) -> dict | None:
        items = self.list_bitacora(case_number)
        return items[0] if items else None

    def add_bitacora_entry(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        nota: str,
        avance_pct: int,
        estado_caso: str,
    ) -> dict[str, Any]:
        cn = self._normalize_case(case_number)
        fk_caso = self.datalake.resolve_fk_caso(cn)
        if not fk_caso:
            raise ValueError("Caso no encontrado")

        avance_pct = max(0, min(100, int(avance_pct)))
        estado = str(estado_caso).strip()
        if estado not in ESTADOS_CASO:
            raise ValueError(f"estado_caso inválido. Use: {ESTADOS_CASO}")

        autor = f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip()
        row = {
            "case_number": cn,
            "fk_caso": fk_caso,
            "fk_usuario": int(user["id_usuario"]),
            "autor_nombre": autor,
            "nota": nota.strip(),
            "avance_pct": avance_pct,
            "estado_caso": estado,
            "fecha_hora": utc_now_iso(),
        }
        created = self.tx.append_row("app_expediente_bitacora", row)

        try:
            self.olap.update_record("dim_caso", str(fk_caso), {"estado_caso": estado})
        except Exception:
            pass

        asig_df = self.tx.read_table("app_asignaciones")
        if not asig_df.empty:
            mask = (
                (asig_df["case_number"].astype(str).str.upper() == cn.upper())
                & (asig_df["estado_asignacion"].astype(str) == "Activa")
            )
            if mask.any():
                asig_df.loc[mask, "estado_caso_snapshot"] = estado
                if "avance_pct_actual" not in asig_df.columns:
                    asig_df["avance_pct_actual"] = 0
                asig_df.loc[mask, "avance_pct_actual"] = avance_pct
                self.tx.write_table("app_asignaciones", asig_df)

        try:
            from packages.dashboard_analitica.services.summary_materializer import (
                refresh_investigation_dashboard_metrics,
            )

            refresh_investigation_dashboard_metrics()
        except Exception:
            pass

        return created
