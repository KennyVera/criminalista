"""
Índice operativo de casos: consultas DuckDB sobre Parquet (sin cargar 300k filas en RAM).
Tabla app_casos_operativos = vista materializada opcional para listados rápidos.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.services.analytics_service import AnalyticsService
from core.services.minio_store import MinioParquetStore
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

DEFAULT_PAGE_SIZE = 40
MIN_SEARCH_LEN = 2


class CasosOperativosStore:
    def __init__(self) -> None:
        self.olap = MinioParquetStore()
        self.tx = TransactionalMinioStore()
        self._analytics = AnalyticsService(self.olap)

    def _dim_caso_uri(self) -> str:
        key = self.olap._object_key("dim_caso")
        return self._analytics._s3_uri(key)

    @staticmethod
    def _escape_like(q: str) -> str:
        return q.replace("'", "''").replace("%", "").replace("_", "")

    def _active_caso_ids(self) -> list[int]:
        df = self.tx.read_table("app_asignaciones")
        if df.empty:
            return []
        active = df[df["estado_asignacion"].astype(str) == "Activa"]
        if active.empty:
            return []
        return [int(x) for x in active["fk_caso"].tolist()]

    def _assignment_by_caso(self) -> dict[int, dict[str, Any]]:
        df = self.tx.read_table("app_asignaciones")
        if df.empty:
            return {}
        active = df[df["estado_asignacion"].astype(str) == "Activa"]
        out: dict[int, dict] = {}
        for row in active.to_dict(orient="records"):
            out[int(row["fk_caso"])] = row
        return out

    def search_casos(
        self,
        *,
        q: str = "",
        page: int = 1,
        per_page: int = DEFAULT_PAGE_SIZE,
        solo_sin_asignar: bool = False,
        solo_asignados: bool = False,
        estado: str = "",
        prioridad: str = "",
    ) -> dict[str, Any]:
        """
        Listado paginado en dim_caso vía DuckDB (OLAP MinIO).
        Permite explorar casos sin recordar el número (página a página).
        """
        if solo_asignados:
            return self._search_casos_asignados(
                q=q,
                page=page,
                per_page=per_page,
                estado=estado,
                prioridad=prioridad,
            )

        page = max(1, page)
        per_page = max(1, min(per_page, 100))
        offset = (page - 1) * per_page
        src = self._dim_caso_uri()

        where_parts: list[str] = []
        q = (q or "").strip()
        if q:
            safe = self._escape_like(q.lower())
            where_parts.append(
                f"LOWER(CAST(case_number AS VARCHAR)) LIKE '%{safe}%'"
            )

        estado = (estado or "").strip()
        if estado:
            safe_est = self._escape_like(estado)
            where_parts.append(
                f"LOWER(CAST(estado_caso AS VARCHAR)) = LOWER('{safe_est}')"
            )

        prioridad = (prioridad or "").strip()
        if prioridad:
            safe_pri = self._escape_like(prioridad)
            where_parts.append(
                f"LOWER(CAST(prioridad_caso AS VARCHAR)) = LOWER('{safe_pri}')"
            )

        exclude_ids = self._active_caso_ids() if solo_sin_asignar else []
        if exclude_ids:
            id_list = ",".join(str(i) for i in exclude_ids[:8000])
            where_parts.append(f"CAST(id AS BIGINT) NOT IN ({id_list})")

        where_sql = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""

        con = self._analytics.connection()
        count_row = con.execute(
            f"SELECT COUNT(*)::BIGINT AS c FROM read_parquet('{src}'){where_sql}"
        ).fetchone()
        total = int(count_row[0]) if count_row else 0

        rows = con.execute(
            f"""
            SELECT
                CAST(id AS BIGINT) AS id,
                CAST(case_number AS VARCHAR) AS case_number,
                CAST(estado_caso AS VARCHAR) AS estado_caso,
                CAST(fecha_reporte AS VARCHAR) AS fecha_reporte,
                CAST(prioridad_caso AS VARCHAR) AS prioridad_caso,
                CAST(investigador_asignado AS VARCHAR) AS investigador_asignado
            FROM read_parquet('{src}')
            {where_sql}
            ORDER BY CAST(id AS BIGINT) DESC
            LIMIT {per_page} OFFSET {offset}
            """
        ).fetchdf()

        asignaciones = self._assignment_by_caso()
        items = []
        for row in rows.to_dict(orient="records"):
            cid = int(row["id"])
            asig = asignaciones.get(cid)
            items.append(
                {
                    "id": cid,
                    "case_number": row.get("case_number"),
                    "estado_caso": row.get("estado_caso"),
                    "fecha_reporte": row.get("fecha_reporte"),
                    "prioridad_caso": row.get("prioridad_caso"),
                    "investigador_asignado": row.get("investigador_asignado"),
                    "asignacion_activa": asig is not None,
                    "fk_detective_actual": int(asig["fk_detective"]) if asig else None,
                    "detective_actual": asig.get("detective_nombre") if asig else None,
                    "fecha_asignacion_actual": asig.get("fecha_asignacion") if asig else None,
                }
            )

        items = self._enrich_items_with_hecho(items)
        total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
        return {
            "items": items,
            "page": page,
            "perPage": per_page,
            "totalItems": total,
            "totalPages": total_pages,
            "requires_search": False,
            "message": (
                f"Mostrando página {page} de {total_pages} ({total:,} casos en total)."
                if total
                else "No hay casos que coincidan con los filtros."
            ).replace(",", "."),
        }

    def _build_filter_clauses(
        self, *, q: str = "", estado: str = "", prioridad: str = ""
    ) -> list[str]:
        where_parts: list[str] = []
        q = (q or "").strip()
        if q:
            safe = self._escape_like(q.lower())
            where_parts.append(
                f"LOWER(CAST(case_number AS VARCHAR)) LIKE '%{safe}%'"
            )

        estado = (estado or "").strip()
        if estado:
            safe_est = self._escape_like(estado)
            where_parts.append(
                f"LOWER(CAST(estado_caso AS VARCHAR)) = LOWER('{safe_est}')"
            )

        prioridad = (prioridad or "").strip()
        if prioridad:
            safe_pri = self._escape_like(prioridad)
            where_parts.append(
                f"LOWER(CAST(prioridad_caso AS VARCHAR)) = LOWER('{safe_pri}')"
            )
        return where_parts

    def _items_from_rows(
        self, rows: pd.DataFrame, asignaciones: dict[int, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        items = []
        for row in rows.to_dict(orient="records"):
            cid = int(row["id"])
            asig = asignaciones.get(cid)
            items.append(
                {
                    "id": cid,
                    "case_number": row.get("case_number"),
                    "estado_caso": row.get("estado_caso"),
                    "fecha_reporte": row.get("fecha_reporte"),
                    "prioridad_caso": row.get("prioridad_caso"),
                    "investigador_asignado": row.get("investigador_asignado"),
                    "asignacion_activa": asig is not None,
                    "fk_detective_actual": int(asig["fk_detective"]) if asig else None,
                    "detective_actual": asig.get("detective_nombre") if asig else None,
                    "fecha_asignacion_actual": asig.get("fecha_asignacion") if asig else None,
                }
            )
        return items

    def _search_casos_asignados(
        self,
        *,
        q: str = "",
        page: int = 1,
        per_page: int = DEFAULT_PAGE_SIZE,
        estado: str = "",
        prioridad: str = "",
    ) -> dict[str, Any]:
        """Solo casos con asignación activa, ordenados por fecha de asignación."""
        page = max(1, page)
        per_page = max(1, min(per_page, 100))
        offset = (page - 1) * per_page

        asignaciones = self._assignment_by_caso()
        if not asignaciones:
            return {
                "items": [],
                "page": page,
                "perPage": per_page,
                "totalItems": 0,
                "totalPages": 1,
                "requires_search": False,
                "filtro_asignacion": "asignados",
                "message": "No hay casos con detective asignado actualmente.",
            }

        assigned_ids = list(asignaciones.keys())
        id_list = ",".join(str(i) for i in assigned_ids[:8000])
        where_parts = self._build_filter_clauses(q=q, estado=estado, prioridad=prioridad)
        where_parts.append(f"CAST(id AS BIGINT) IN ({id_list})")
        where_sql = f" WHERE {' AND '.join(where_parts)}"

        src = self._dim_caso_uri()
        con = self._analytics.connection()
        rows = con.execute(
            f"""
            SELECT
                CAST(id AS BIGINT) AS id,
                CAST(case_number AS VARCHAR) AS case_number,
                CAST(estado_caso AS VARCHAR) AS estado_caso,
                CAST(fecha_reporte AS VARCHAR) AS fecha_reporte,
                CAST(prioridad_caso AS VARCHAR) AS prioridad_caso,
                CAST(investigador_asignado AS VARCHAR) AS investigador_asignado
            FROM read_parquet('{src}')
            {where_sql}
            """
        ).fetchdf()

        items = self._items_from_rows(rows, asignaciones)
        items.sort(
            key=lambda x: str(x.get("fecha_asignacion_actual") or ""),
            reverse=True,
        )
        total = len(items)
        total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
        page_items = items[offset : offset + per_page]
        page_items = self._enrich_items_with_hecho(page_items)

        return {
            "items": page_items,
            "page": page,
            "perPage": per_page,
            "totalItems": total,
            "totalPages": total_pages,
            "requires_search": False,
            "filtro_asignacion": "asignados",
            "message": (
                f"Casos asignados: página {page} de {total_pages} ({total:,} en total)."
                if total
                else "Ningún caso asignado coincide con los filtros."
            ).replace(",", "."),
        }

    def _enrich_items_with_hecho(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Agrega tipo delictivo, distrito y fecha del hecho (OLAP star schema)."""
        if not items:
            return items
        numbers = [
            str(i.get("case_number") or "").strip()
            for i in items
            if i.get("case_number")
        ]
        if not numbers:
            return items

        by_cn = self._analytics.lookup_hechos_by_case_numbers(numbers)
        if not by_cn:
            return items

        for item in items:
            cn = str(item.get("case_number") or "").strip().upper()
            extra = by_cn.get(cn)
            if not extra:
                continue
            item["primary_type"] = extra.get("primary_type")
            item["descripcion_delito"] = extra.get("description")
            item["district"] = extra.get("district")
            item["beat"] = extra.get("beat")
            item["fecha_hecho"] = extra.get("date")
            item["anio_hecho"] = extra.get("year")
            item["ward"] = extra.get("ward")
            item["block"] = extra.get("block")
            item["location_description"] = extra.get("location_description")
        return items

    def get_caso_by_id(self, fk_caso: int) -> dict[str, Any] | None:
        """Un solo caso por ID (DuckDB, sin cargar el dataset completo)."""
        src = self._dim_caso_uri()
        con = self._analytics.connection()
        df = con.execute(
            f"""
            SELECT *
            FROM read_parquet('{src}')
            WHERE CAST(id AS BIGINT) = {int(fk_caso)}
            LIMIT 1
            """
        ).fetchdf()
        if df.empty:
            return self.olap.get_record("dim_caso", str(fk_caso))
        row = df.iloc[0].to_dict()
        return {k: (None if pd.isna(v) else v) for k, v in row.items()}

    def refresh_materialized_index(self, *, limit: int | None = None) -> dict[str, Any]:
        """
        Materializa app_casos_operativos (columnas mínimas) para respaldos y consultas locales.
        """
        src = self._dim_caso_uri()
        con = self._analytics.connection()
        lim = f"LIMIT {int(limit)}" if limit else ""
        df = con.execute(
            f"""
            SELECT
                CAST(id AS BIGINT) AS id,
                CAST(case_number AS VARCHAR) AS case_number,
                CAST(estado_caso AS VARCHAR) AS estado_caso,
                CAST(fecha_reporte AS VARCHAR) AS fecha_reporte,
                CAST(prioridad_caso AS VARCHAR) AS prioridad_caso,
                CAST(investigador_asignado AS VARCHAR) AS investigador_asignado
            FROM read_parquet('{src}')
            ORDER BY id DESC
            {lim}
            """
        ).fetchdf()
        if df.empty:
            return {"rows": 0, "message": "dim_caso vacío"}

        df["indexado_en"] = utc_now_iso()
        self.tx.ensure_tables()
        self.tx.write_table("app_casos_operativos", df)
        return {
            "rows": len(df),
            "message": f"Índice operativo actualizado ({len(df):,} casos).".replace(",", "."),
        }
