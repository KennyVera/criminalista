"""Bitácora de accesos (login, logout, intentos fallidos) — app_bitacora_acceso."""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

TIPO_LOGIN = "login"
TIPO_LOGOUT = "logout"
TIPO_LOGIN_FALLIDO = "login_fallido"
TIPO_BLOQUEO = "cuenta_bloqueada"
TIPO_MFA_ENVIADO = "mfa_enviado"
TIPO_MFA_FALLIDO = "mfa_fallido"
TIPO_SESION_CERRADA_ADMIN = "sesion_cerrada_admin"


class BitacoraAccesoService:
    def __init__(self, store: TransactionalMinioStore | None = None) -> None:
        self.tx = store or TransactionalMinioStore()
        self.tx.ensure_tables()

    def record(
        self,
        *,
        tipo_evento: str,
        exito: bool,
        fk_usuario: int | None = None,
        email: str | None = None,
        direccion_ip: str | None = None,
        user_agent: str | None = None,
        detalle: str = "",
    ) -> dict[str, Any]:
        return self.tx.append_row(
            "app_bitacora_acceso",
            {
                "fk_usuario": fk_usuario,
                "email": (email or "").strip().lower(),
                "tipo_evento": tipo_evento,
                "exito": bool(exito),
                "direccion_ip": direccion_ip or "",
                "user_agent": (user_agent or "")[:500],
                "detalle": detalle,
                "fecha_hora": utc_now_iso(),
            },
        )

    def list_events(
        self,
        *,
        email: str | None = None,
        fk_usuario: int | None = None,
        tipo_evento: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        df = self.tx.read_table("app_bitacora_acceso")
        if df.empty:
            return []
        if email:
            df = df[df["email"].astype(str).str.lower() == email.strip().lower()]
        if fk_usuario is not None:
            df = df[pd.to_numeric(df["fk_usuario"], errors="coerce") == int(fk_usuario)]
        if tipo_evento:
            df = df[df["tipo_evento"].astype(str) == tipo_evento.strip()]
        if "fecha_hora" in df.columns:
            df = df.sort_values("fecha_hora", ascending=False)
        return df.head(int(limit)).to_dict(orient="records")
