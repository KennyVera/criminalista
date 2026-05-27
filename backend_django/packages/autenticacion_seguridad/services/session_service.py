from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

SESSION_CLOSED_BY_ADMIN_MSG = (
    "Su sesión en el sistema ha finalizado. Vuelva a Iniciar Sesión"
)
MOTIVO_ADMIN = "admin_cerrada"
MOTIVO_LOGOUT = "logout"
MOTIVO_EXPIRED = "expirada"


def _parse_iso(value: str) -> datetime | None:
    if not value or pd.isna(value):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


class SessionService:
    def __init__(self, store: TransactionalMinioStore | None = None) -> None:
        self.store = store or TransactionalMinioStore()

    def new_jti(self) -> str:
        return str(uuid.uuid4())

    def open_session(
        self,
        *,
        user: dict[str, Any],
        nombre_rol: str,
        jti: str,
        ip: str | None,
        user_agent: str | None,
        fecha_expiracion: str,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        row = {
            "fk_usuario": int(user["id_usuario"]),
            "token_jti": jti,
            "email": user["email"],
            "nombre_rol": nombre_rol,
            "numero_placa": user["numero_placa"],
            "nombres": user["nombres"],
            "apellidos": user["apellidos"],
            "direccion_ip": ip or "",
            "user_agent": (user_agent or "")[:500],
            "fecha_inicio": now,
            "fecha_ultimo_acceso": now,
            "fecha_expiracion": fecha_expiracion,
            "activa": True,
            "fecha_cierre": "",
            "motivo_cierre": "",
        }
        return self.store.append_row("app_sesiones_activas", row)

    def _ensure_motivo_column(self, df: pd.DataFrame) -> pd.DataFrame:
        if "motivo_cierre" not in df.columns:
            df["motivo_cierre"] = ""
        return df

    def close_session(self, jti: str, *, motivo: str = MOTIVO_LOGOUT) -> bool:
        df = self._ensure_motivo_column(self.store.read_table("app_sesiones_activas"))
        if df.empty:
            return False
        mask = df["token_jti"].astype(str) == jti
        if not mask.any():
            return False
        df.loc[mask, "activa"] = False
        df.loc[mask, "fecha_cierre"] = utc_now_iso()
        df.loc[mask, "motivo_cierre"] = motivo
        self.store.write_table("app_sesiones_activas", df)
        return True

    def close_session_by_id(self, id_sesion: int, *, motivo: str = MOTIVO_ADMIN) -> bool:
        df = self._ensure_motivo_column(self.store.read_table("app_sesiones_activas"))
        mask = df["id_sesion"] == id_sesion
        if not mask.any():
            return False
        jti = str(df.loc[mask, "token_jti"].iloc[0])
        return self.close_session(jti, motivo=motivo)

    def get_session_status(self, jti: str) -> dict[str, Any]:
        """Estado de la sesión para polling del cliente."""
        df = self._ensure_motivo_column(self.store.read_table("app_sesiones_activas"))
        if df.empty:
            return {
                "valid": False,
                "code": "SESSION_REVOKED",
                "message": SESSION_CLOSED_BY_ADMIN_MSG,
            }
        mask = df["token_jti"].astype(str) == jti
        if not mask.any():
            return {
                "valid": False,
                "code": "SESSION_REVOKED",
                "message": SESSION_CLOSED_BY_ADMIN_MSG,
            }
        row = df.loc[mask].iloc[0]
        active_mask = str(row.get("activa", "")).lower() in ("true", "1", "1.0")
        if not active_mask:
            motivo = str(row.get("motivo_cierre", "") or "")
            if motivo == MOTIVO_ADMIN:
                return {
                    "valid": False,
                    "code": "SESSION_REVOKED",
                    "message": SESSION_CLOSED_BY_ADMIN_MSG,
                }
            return {
                "valid": False,
                "code": "SESSION_EXPIRED",
                "message": "Su sesión ha expirado. Vuelva a Iniciar Sesión",
            }
        exp = _parse_iso(str(row.get("fecha_expiracion", "")))
        if exp and exp < datetime.now(timezone.utc):
            self.close_session(jti, motivo=MOTIVO_EXPIRED)
            return {
                "valid": False,
                "code": "SESSION_EXPIRED",
                "message": "Su sesión ha expirado. Vuelva a Iniciar Sesión",
            }
        return {"valid": True}

    def touch_session(self, jti: str) -> None:
        df = self.store.read_table("app_sesiones_activas")
        if df.empty:
            return
        active_mask = df["activa"].astype(str).str.lower().isin(("true", "1", "1.0"))
        mask = (df["token_jti"].astype(str) == jti) & active_mask
        if mask.any():
            df.loc[mask, "fecha_ultimo_acceso"] = utc_now_iso()
            self.store.write_table("app_sesiones_activas", df)

    def is_session_active(self, jti: str) -> bool:
        self._expire_stale_sessions()
        df = self.store.read_table("app_sesiones_activas")
        if df.empty:
            return False
        active_mask = df["activa"].astype(str).str.lower().isin(("true", "1", "1.0"))
        hits = df[(df["token_jti"].astype(str) == jti) & active_mask]
        if hits.empty:
            return False
        exp = _parse_iso(str(hits.iloc[0].get("fecha_expiracion", "")))
        if exp and exp < datetime.now(timezone.utc):
            self.close_session(jti, motivo=MOTIVO_EXPIRED)
            return False
        return True

    def _expire_stale_sessions(self) -> None:
        df = self.store.read_table("app_sesiones_activas")
        if df.empty:
            return
        now = datetime.now(timezone.utc)
        changed = False
        active_mask = df["activa"].astype(str).str.lower().isin(("true", "1", "1.0"))
        for idx, row in df[active_mask].iterrows():
            exp = _parse_iso(str(row.get("fecha_expiracion", "")))
            if exp and exp < now:
                df.at[idx, "activa"] = False
                df.at[idx, "fecha_cierre"] = utc_now_iso()
                changed = True
        if changed:
            self.store.write_table("app_sesiones_activas", df)

    def list_active_sessions(self) -> list[dict[str, Any]]:
        self._expire_stale_sessions()
        df = self.store.read_table("app_sesiones_activas")
        if df.empty:
            return []
        active_mask = df["activa"].astype(str).str.lower().isin(("true", "1", "1.0"))
        active = df[active_mask].copy()
        if active.empty:
            return []
        active = active.sort_values("fecha_ultimo_acceso", ascending=False)
        rows = active.to_dict(orient="records")
        for row in rows:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
                elif hasattr(v, "item"):
                    try:
                        row[k] = v.item()
                    except Exception:
                        pass
        return rows
