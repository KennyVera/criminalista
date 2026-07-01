"""Personal policial (datos laborales) — separado de app_usuarios."""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso


class PersonalPolicialService:
    def __init__(self, store: TransactionalMinioStore | None = None) -> None:
        self.tx = store or TransactionalMinioStore()
        self.tx.ensure_tables()

    def list_rangos(self, *, activo_only: bool = True) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_rangos_policiales")
        if activo_only and not df.empty:
            df = df[df["activo"].astype(str).str.lower().isin(("true", "1", "si", "sí"))]
        if not df.empty and "nivel_jerarquico" in df.columns:
            df = df.sort_values("nivel_jerarquico")
        return df.to_dict(orient="records")

    def list_personal(
        self,
        *,
        fk_distrito: int | None = None,
        fk_estacion: int | None = None,
        activo_only: bool = True,
    ) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_personal_policial")
        if fk_distrito is not None and not df.empty:
            df = df[pd.to_numeric(df["fk_distrito"], errors="coerce") == int(fk_distrito)]
        if fk_estacion is not None and not df.empty:
            df = df[pd.to_numeric(df["fk_estacion"], errors="coerce") == int(fk_estacion)]
        if activo_only and not df.empty:
            df = df[df["activo"].astype(str).str.lower().isin(("true", "1", "si", "sí"))]
        return df.to_dict(orient="records")

    def get_by_usuario(self, fk_usuario: int) -> dict[str, Any] | None:
        df = self.tx.read_table("app_personal_policial")
        if df.empty:
            return None
        hits = df[pd.to_numeric(df["fk_usuario"], errors="coerce") == int(fk_usuario)]
        return hits.iloc[0].to_dict() if not hits.empty else None

    def create_personal(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        row = {
            "fk_usuario": int(data["fk_usuario"]) if data.get("fk_usuario") not in (None, "") else None,
            "fk_rango": int(data["fk_rango"]),
            "fk_estacion": int(data.get("fk_estacion") or 0) or None,
            "fk_distrito": int(data.get("fk_distrito") or 0) or None,
            "fk_departamento": int(data.get("fk_departamento") or 0) or None,
            "numero_placa": str(data.get("numero_placa", "")).strip().upper(),
            "nombres": str(data.get("nombres", "")).strip(),
            "apellidos": str(data.get("apellidos", "")).strip(),
            "identificacion": str(data.get("identificacion", "")).strip(),
            "email_laboral": str(data.get("email_laboral", "")).strip().lower(),
            "telefono": str(data.get("telefono", "")).strip(),
            "fecha_ingreso": str(data.get("fecha_ingreso", now[:10])),
            "estado_laboral": str(data.get("estado_laboral", "Activo")),
            "activo": bool(data.get("activo", True)),
            "fecha_creacion": now,
            "fecha_actualizacion": now,
        }
        if not row["numero_placa"] or not row["nombres"]:
            raise ValueError("numero_placa y nombres son obligatorios")
        return self.tx.append_row("app_personal_policial", row)

    def update_personal(self, id_personal: int, data: dict[str, Any]) -> dict[str, Any] | None:
        df = self.tx.read_table("app_personal_policial")
        mask = pd.to_numeric(df["id_personal"], errors="coerce") == int(id_personal)
        if not mask.any():
            return None
        for key, value in data.items():
            if key in df.columns and key != "id_personal":
                df.loc[mask, key] = value
        df.loc[mask, "fecha_actualizacion"] = utc_now_iso()
        self.tx.write_table("app_personal_policial", df)
        return df[mask].iloc[0].to_dict()
