"""
Consulta hechos crudos en el Data Lake (MinIO Parquet crimes_220k) por case_number.
Enriquecimiento OLAP (fact consolidado + dimensiones) cuando el raw no está exportado.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.services.analytics_service import AnalyticsService
from core.services.minio_store import MinioParquetStore


class ExpedienteDatalakeService:
    def __init__(self) -> None:
        self.store = MinioParquetStore()
        self._analytics = AnalyticsService(self.store)

    def _crimes_uri(self) -> str:
        return self._analytics._s3_uri(self.store._object_key("crimes_220k"))

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("'", "''").strip()

    @staticmethod
    def _is_blank(value: Any) -> bool:
        if value is None:
            return True
        s = str(value).strip()
        return not s or s == "—"

    @staticmethod
    def _merge_resumen(base: dict[str, Any], olap: dict[str, Any] | None) -> dict[str, Any]:
        if not olap:
            return base
        merged = dict(base)
        for key, val in olap.items():
            if ExpedienteDatalakeService._is_blank(merged.get(key)) and not ExpedienteDatalakeService._is_blank(val):
                merged[key] = val
        return merged

    @staticmethod
    def _resumen_from_olap(case_number: str, olap: dict[str, Any]) -> dict[str, Any]:
        return {
            "case_number": case_number,
            "primary_type": olap.get("primary_type"),
            "description": olap.get("description") or olap.get("observaciones"),
            "date": olap.get("date") or olap.get("fecha_reporte"),
            "district": olap.get("district"),
            "beat": olap.get("beat"),
            "ward": olap.get("ward"),
            "block": olap.get("block"),
            "location_description": olap.get("location_description"),
            "latitude": olap.get("latitude"),
            "longitude": olap.get("longitude"),
            "location": olap.get("location"),
            "arrest": olap.get("arrest"),
            "domestic": olap.get("domestic"),
            "year": olap.get("year"),
            "iucr": olap.get("iucr"),
            "fbi_code": olap.get("fbi_code"),
            "estado_caso": olap.get("estado_caso"),
            "prioridad_caso": olap.get("prioridad_caso"),
            "investigador_asignado": olap.get("investigador_asignado"),
            "total_registros_lake": 1,
        }

    def get_hechos_by_case_number(self, case_number: str, *, limit: int = 20) -> dict[str, Any]:
        cn = self._escape(case_number)
        if not cn:
            raise ValueError("case_number requerido")

        olap = self._analytics.lookup_hecho_by_case_number(case_number)
        raw_hechos: list[dict[str, Any]] = []

        src = self._crimes_uri()
        con = self._analytics.connection()
        try:
            rows_df = con.execute(
                f"""
                SELECT *
                FROM read_parquet('{src}')
                WHERE UPPER(TRIM(CAST(case_number AS VARCHAR))) = UPPER(TRIM('{cn}'))
                LIMIT {int(limit)}
                """
            ).fetchdf()
            if not rows_df.empty:
                for row in rows_df.to_dict(orient="records"):
                    raw_hechos.append(
                        {k: (None if pd.isna(v) else v) for k, v in row.items()}
                    )
        except Exception:
            raw_hechos = []

        if raw_hechos:
            first = raw_hechos[0]
            resumen = {
                "case_number": first.get("case_number") or case_number,
                "primary_type": first.get("primary_type"),
                "description": first.get("description"),
                "date": first.get("date"),
                "district": first.get("district"),
                "beat": first.get("beat"),
                "ward": first.get("ward"),
                "block": first.get("block"),
                "location_description": first.get("location_description"),
                "latitude": first.get("latitude"),
                "longitude": first.get("longitude"),
                "location": first.get("location"),
                "arrest": first.get("arrest"),
                "domestic": first.get("domestic"),
                "year": first.get("year"),
                "iucr": first.get("iucr"),
                "fbi_code": first.get("fbi_code"),
                "total_registros_lake": len(raw_hechos),
            }
            resumen = self._merge_resumen(resumen, olap)
            if olap:
                for k in ("estado_caso", "prioridad_caso", "investigador_asignado"):
                    if self._is_blank(resumen.get(k)):
                        resumen[k] = olap.get(k)
            return {
                "case_number": case_number,
                "found": True,
                "hechos": raw_hechos,
                "resumen": resumen,
                "source": "minio:crimes_220k+olap" if olap else "minio:crimes_220k",
            }

        if olap:
            resumen = self._resumen_from_olap(case_number, olap)
            return {
                "case_number": case_number,
                "found": True,
                "hechos": [olap],
                "resumen": resumen,
                "source": "minio:olap",
            }

        return self._fallback_from_dim_caso(case_number)

    def resolve_fk_caso(self, case_number: str) -> int | None:
        """ID en dim_caso para tablas transaccionales."""
        src = self._analytics._s3_uri(self.store._object_key("dim_caso"))
        cn = self._escape(case_number)
        con = self._analytics.connection()
        row = con.execute(
            f"""
            SELECT CAST(id AS BIGINT) AS id
            FROM read_parquet('{src}')
            WHERE UPPER(TRIM(CAST(case_number AS VARCHAR))) = UPPER(TRIM('{cn}'))
            LIMIT 1
            """
        ).fetchone()
        return int(row[0]) if row else None

    def _fallback_from_dim_caso(self, case_number: str) -> dict[str, Any]:
        """Último recurso: solo metadatos de dim_caso (sin join a fact)."""
        cn = self._escape(case_number)
        src = self._analytics._s3_uri(self.store._object_key("dim_caso"))
        con = self._analytics.connection()
        df = con.execute(
            f"""
            SELECT *
            FROM read_parquet('{src}')
            WHERE UPPER(TRIM(CAST(case_number AS VARCHAR))) = UPPER(TRIM('{cn}'))
            LIMIT 1
            """
        ).fetchdf()
        if df.empty:
            return {
                "case_number": case_number,
                "found": False,
                "hechos": [],
                "resumen": None,
                "message": "No hay registros en el Data Lake para este número de caso.",
            }
        row = {k: (None if pd.isna(v) else v) for k, v in df.iloc[0].to_dict().items()}
        resumen = {
            "case_number": row.get("case_number") or case_number,
            "primary_type": None,
            "description": row.get("observaciones"),
            "date": row.get("fecha_reporte"),
            "district": None,
            "beat": None,
            "ward": None,
            "block": None,
            "location_description": None,
            "latitude": None,
            "longitude": None,
            "location": None,
            "arrest": None,
            "domestic": None,
            "year": None,
            "iucr": None,
            "fbi_code": None,
            "total_registros_lake": 0,
            "estado_caso": row.get("estado_caso"),
            "prioridad_caso": row.get("prioridad_caso"),
            "investigador_asignado": row.get("investigador_asignado"),
        }
        return {
            "case_number": case_number,
            "found": True,
            "hechos": [row],
            "resumen": resumen,
            "source": "minio:dim_caso",
            "note": "Solo metadatos del caso; ejecute ETL para enlazar hechos OLAP.",
        }
