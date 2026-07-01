"""Departamentos, distritos y estaciones policiales."""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso


class OrganizacionPolicialService:
    def __init__(self, store: TransactionalMinioStore | None = None) -> None:
        self.tx = store or TransactionalMinioStore()
        self.tx.ensure_tables()

    def list_departamentos(self, *, activo_only: bool = True) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_departamentos_policiales")
        if activo_only and not df.empty:
            df = df[df["activo"].astype(str).str.lower().isin(("true", "1", "si", "sí"))]
        return df.to_dict(orient="records")

    def list_distritos(
        self, *, fk_departamento: int | None = None, activo_only: bool = True
    ) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_distritos_policiales")
        if fk_departamento is not None and not df.empty:
            df = df[pd.to_numeric(df["fk_departamento"], errors="coerce") == int(fk_departamento)]
        if activo_only and not df.empty:
            df = df[df["activo"].astype(str).str.lower().isin(("true", "1", "si", "sí"))]
        return df.to_dict(orient="records")

    def list_estaciones(
        self, *, fk_distrito: int | None = None, activo_only: bool = True
    ) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_estaciones_policiales")
        if fk_distrito is not None and not df.empty:
            df = df[pd.to_numeric(df["fk_distrito"], errors="coerce") == int(fk_distrito)]
        if activo_only and not df.empty:
            df = df[df["activo"].astype(str).str.lower().isin(("true", "1", "si", "sí"))]
        return df.to_dict(orient="records")

    def create_departamento(self, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "codigo": str(data.get("codigo", "")).strip().upper(),
            "nombre": str(data.get("nombre", "")).strip(),
            "ciudad": str(data.get("ciudad", "")).strip(),
            "estado_region": str(data.get("estado_region", "")).strip(),
            "pais": str(data.get("pais", "USA")).strip(),
            "activo": bool(data.get("activo", True)),
            "fecha_creacion": utc_now_iso(),
        }
        if not row["codigo"] or not row["nombre"]:
            raise ValueError("codigo y nombre son obligatorios")
        return self.tx.append_row("app_departamentos_policiales", row)

    def create_distrito(self, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "fk_departamento": int(data["fk_departamento"]),
            "codigo": str(data.get("codigo", "")).strip(),
            "nombre": str(data.get("nombre", "")).strip(),
            "descripcion": str(data.get("descripcion", "")).strip(),
            "activo": bool(data.get("activo", True)),
        }
        if not row["codigo"] or not row["nombre"]:
            raise ValueError("codigo y nombre son obligatorios")
        return self.tx.append_row("app_distritos_policiales", row)

    def create_estacion(self, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "fk_distrito": int(data["fk_distrito"]),
            "codigo": str(data.get("codigo", "")).strip().upper(),
            "nombre": str(data.get("nombre", "")).strip(),
            "direccion": str(data.get("direccion", "")).strip(),
            "telefono": str(data.get("telefono", "")).strip(),
            "activo": bool(data.get("activo", True)),
        }
        if not row["codigo"] or not row["nombre"]:
            raise ValueError("codigo y nombre son obligatorios")
        return self.tx.append_row("app_estaciones_policiales", row)
