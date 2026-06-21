from __future__ import annotations

import os
from typing import Any

import pandas as pd

from core.services.minio_store import MinioParquetStore
from packages.expedientes_criminales.services.datalake_service import ExpedienteDatalakeService
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

TIPOS_INVOLUCRADO = ("Víctima", "Testigo", "Sospechoso")
ESTADOS_CASO = ("Abierto", "En investigación", "Resuelto", "Cerrado", "Archivado")
# RN-09: estados que implican cierre del expediente y exigen criterios de completitud.
ESTADOS_CIERRE = ("Cerrado", "Archivado")


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
        # Delegado al paquete P06 (evidencias_digitales) — fuente única de verdad.
        from packages.evidencias_digitales.services.evidencias_service import EvidenciasService

        return EvidenciasService().list_by_case(case_number)

    def upload_evidencia(
        self,
        case_number: str,
        *,
        user: dict[str, Any],
        file_obj: Any,
        filename: str,
        tipo_evidencia: str = "Multimedia",
    ) -> dict[str, Any]:
        # Delegado al paquete P06: calcula hash SHA-256 e inicia la cadena de custodia.
        from packages.evidencias_digitales.services.evidencias_service import EvidenciasService

        return EvidenciasService().upload(
            case_number,
            user=user,
            file_obj=file_obj,
            filename=filename,
            tipo_evidencia=tipo_evidencia,
        )

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

    def check_close_requirements(self, case_number: str, *, avance_pct: int | None = None) -> dict[str, Any]:
        """RN-09: valida los criterios de completitud y custodia para cerrar un expediente.

        Devuelve {"ok": bool, "faltantes": [str], "checks": {...}}.
        """
        cn = self._normalize_case(case_number)
        involucrados = self.list_involucrados(cn)
        evidencias = self.list_evidencias(cn)

        tiene_involucrados = len(involucrados) > 0
        tiene_evidencias = len(evidencias) > 0
        # Custodia: ninguna evidencia debe haber quedado fuera de custodia (p.ej. "Destruida").
        custodia_ok = all(
            str(ev.get("estado_custodia") or "").strip().lower() != "destruida"
            for ev in evidencias
        )
        avance_ok = True if avance_pct is None else int(avance_pct) >= 100

        faltantes: list[str] = []
        if not tiene_involucrados:
            faltantes.append("Debe registrar al menos un involucrado (víctima, sospechoso o testigo).")
        if not tiene_evidencias:
            faltantes.append("Debe cargar al menos una evidencia digital.")
        if not custodia_ok:
            faltantes.append("Hay evidencias con custodia rota (estado «Destruida»); revise la cadena de custodia.")
        if not avance_ok:
            faltantes.append("El avance del caso debe ser 100% para cerrarlo.")

        return {
            "ok": not faltantes,
            "faltantes": faltantes,
            "checks": {
                "involucrados": tiene_involucrados,
                "evidencias": tiene_evidencias,
                "custodia": custodia_ok,
                "avance": avance_ok,
            },
        }

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

        # RN-09 (CU-O25): solo se puede cerrar si cumple completitud y custodia.
        if estado in ESTADOS_CIERRE:
            req = self.check_close_requirements(cn, avance_pct=avance_pct)
            if not req["ok"]:
                raise ValueError(
                    "No se puede cerrar el expediente (RN-09). " + " ".join(req["faltantes"])
                )

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

        try:
            from core.cache.invalidation import bump_cache_generation

            bump_cache_generation()
        except Exception:
            pass

        return created
