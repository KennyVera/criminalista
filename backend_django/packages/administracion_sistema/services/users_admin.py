from __future__ import annotations

import re
from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.email_validation import validate_email_address
from packages.autenticacion_seguridad.services.auth_service import AuthService
from packages.autenticacion_seguridad.services.passwords import hash_password
from packages.autenticacion_seguridad.services.security_policy import (
    validate_password_strength,
)
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso

ROLE_PLACA_PREFIX: dict[int, str] = {
    1: "CPD",
    2: "CPD",
    3: "CPD",
    4: "OF",
    5: "AN",
}


class UsersAdminService:
    def __init__(self) -> None:
        self.store = TransactionalMinioStore()

    def _users_df(self) -> pd.DataFrame:
        return AuthService._normalize_users_df(self.store.read_table("app_usuarios"))

    def list_users(self) -> list[dict[str, Any]]:
        df = self._users_df()
        roles = self._roles_map()
        prof_df = self.store.read_table("app_perfiles_usuario")
        profile_meta: dict[int, dict[str, Any]] = {}
        if not prof_df.empty:
            for row in prof_df.to_dict(orient="records"):
                uid = int(row["fk_usuario"])
                foto_url = str(row.get("foto_url") or "").strip()
                tiene_foto = bool(foto_url)
                actualizado = row.get("actualizado_en")
                profile_meta[uid] = {
                    "tiene_foto": tiene_foto,
                    "foto_actualizada_en": actualizado if tiene_foto else None,
                }
        items = []
        for row in df.to_dict(orient="records"):
            pub = self._public(row, roles)
            meta = profile_meta.get(int(row["id_usuario"]), {})
            pub["tiene_foto"] = bool(meta.get("tiene_foto"))
            pub["foto_actualizada_en"] = meta.get("foto_actualizada_en")
            items.append(pub)
        return items

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        df = self._users_df()
        row = df[df["id_usuario"] == user_id]
        if row.empty:
            return None
        return self._public(row.iloc[0].to_dict(), self._roles_map())

    def create_user(self, data: dict[str, Any]) -> dict[str, Any]:
        email = validate_email_address(str(data["email"]))
        if self._email_exists(email):
            raise ValueError("El correo ya está registrado")
        fk_rol = int(data["fk_rol"])
        numero_placa = str(data.get("numero_placa") or "").strip().upper()
        if not numero_placa:
            numero_placa = self.generate_numero_placa(fk_rol)
        else:
            self._assert_placa_available(numero_placa)
        password = data.get("password") or "CrimeTrack2026!"
        validate_password_strength(str(password))
        row = {
            "fk_rol": fk_rol,
            "numero_placa": numero_placa,
            "nombres": str(data["nombres"]).strip(),
            "apellidos": str(data["apellidos"]).strip(),
            "email": email,
            "password_hash": hash_password(password),
            "estado_cuenta": data.get("estado_cuenta", "Activa"),
            "intentos_login_fallidos": 0,
            "fecha_creacion": utc_now_iso(),
        }
        created = self.store.append_row("app_usuarios", row)
        return self._public(created, self._roles_map())

    def update_user(self, user_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        df = self._users_df()
        mask = df["id_usuario"] == user_id
        if not mask.any():
            return None
        if "email" in data:
            email = validate_email_address(str(data["email"]))
            other = df[(df["email"].str.lower() == email) & (df["id_usuario"] != user_id)]
            if not other.empty:
                raise ValueError("El correo ya está en uso")
            df.loc[mask, "email"] = email
        if "numero_placa" in data:
            placa = str(data["numero_placa"]).strip().upper()
            current = str(df.loc[mask, "numero_placa"].iloc[0]).strip().upper()
            if placa != current:
                raise ValueError("El número de placa no se puede modificar")
        for field in (
            "fk_rol",
            "nombres",
            "apellidos",
            "estado_cuenta",
            "intentos_login_fallidos",
        ):
            if field in data:
                df.loc[mask, field] = data[field]
        if data.get("password"):
            pwd = str(data["password"])
            validate_password_strength(pwd)
            df.loc[mask, "password_hash"] = hash_password(pwd)
        if str(data.get("estado_cuenta", "")).strip().lower() in ("activa", "active"):
            if "intentos_login_fallidos" not in data:
                df.loc[mask, "intentos_login_fallidos"] = 0
        self.store.write_table("app_usuarios", df)
        return self.get_user(user_id)

    def delete_user(self, user_id: int) -> bool:
        df = self._users_df()
        if user_id == 1:
            raise ValueError("No se puede eliminar el administrador principal")
        before = len(df)
        df = df[df["id_usuario"] != user_id]
        if len(df) == before:
            return False
        self.store.write_table("app_usuarios", df)
        return True

    def set_account_status(self, user_id: int, activa: bool) -> dict[str, Any] | None:
        estado = "Activa" if activa else "Inactiva"
        payload: dict[str, Any] = {"estado_cuenta": estado}
        if activa:
            payload["intentos_login_fallidos"] = 0
        return self.update_user(user_id, payload)

    def generate_numero_placa(self, fk_rol: int) -> str:
        fk_rol = int(fk_rol)
        prefix = ROLE_PLACA_PREFIX.get(fk_rol, "CPD")
        base = fk_rol * 1000
        existing = self._existing_placas()
        for seq in range(1, 10_000):
            candidate = f"{prefix}-{base + seq}"
            if candidate not in existing:
                return candidate
        raise ValueError("No hay números de placa disponibles para este rol")

    def _existing_placas(self) -> set[str]:
        df = self._users_df()
        if df.empty:
            return set()
        return {
            self._normalize_placa(v)
            for v in df["numero_placa"].astype(str).tolist()
            if str(v).strip()
        }

    @staticmethod
    def _normalize_placa(placa: str) -> str:
        return re.sub(r"\s+", "", str(placa or "").strip().upper())

    def _assert_placa_available(self, placa: str, exclude_user_id: int | None = None) -> None:
        normalized = self._normalize_placa(placa)
        if not normalized:
            raise ValueError("El número de placa es obligatorio")
        df = self._users_df()
        if df.empty:
            return
        placas = df["numero_placa"].astype(str).map(self._normalize_placa)
        mask = placas == normalized
        if exclude_user_id is not None:
            mask &= df["id_usuario"] != exclude_user_id
        if mask.any():
            raise ValueError("El número de placa ya está asignado a otro usuario")

    def _email_exists(self, email: str) -> bool:
        df = self._users_df()
        return df["email"].astype(str).str.lower().eq(email).any()

    def _roles_map(self) -> dict[int, str]:
        df = self.store.read_table("app_roles")
        if df.empty:
            return {}
        return {int(r.id_rol): str(r.nombre_rol) for r in df.itertuples(index=False)}

    @staticmethod
    def _public(row: dict, roles: dict[int, str]) -> dict[str, Any]:
        uid = int(row["id_usuario"])
        fk_rol = int(row["fk_rol"])
        return {
            "id_usuario": uid,
            "fk_rol": fk_rol,
            "nombre_rol": roles.get(fk_rol, ""),
            "numero_placa": row["numero_placa"],
            "nombres": row["nombres"],
            "apellidos": row["apellidos"],
            "email": row["email"],
            "estado_cuenta": row["estado_cuenta"],
            "intentos_login_fallidos": int(row.get("intentos_login_fallidos") or 0),
            "fecha_creacion": row.get("fecha_creacion"),
        }
