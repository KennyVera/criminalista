from __future__ import annotations

from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.auth_service import AuthService
from packages.autenticacion_seguridad.services.passwords import hash_password
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso


class UsersAdminService:
    def __init__(self) -> None:
        self.store = TransactionalMinioStore()

    def _users_df(self) -> pd.DataFrame:
        return AuthService._normalize_users_df(self.store.read_table("app_usuarios"))

    def list_users(self) -> list[dict[str, Any]]:
        df = self._users_df()
        roles = self._roles_map()
        items = []
        for row in df.to_dict(orient="records"):
            items.append(self._public(row, roles))
        return items

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        df = self._users_df()
        row = df[df["id_usuario"] == user_id]
        if row.empty:
            return None
        return self._public(row.iloc[0].to_dict(), self._roles_map())

    def create_user(self, data: dict[str, Any]) -> dict[str, Any]:
        email = str(data["email"]).strip().lower()
        if self._email_exists(email):
            raise ValueError("El correo ya está registrado")
        password = data.get("password") or "CrimeTrack2026!"
        row = {
            "fk_rol": int(data["fk_rol"]),
            "numero_placa": str(data["numero_placa"]).strip(),
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
            email = str(data["email"]).strip().lower()
            other = df[(df["email"].str.lower() == email) & (df["id_usuario"] != user_id)]
            if not other.empty:
                raise ValueError("El correo ya está en uso")
            df.loc[mask, "email"] = email
        for field in (
            "fk_rol",
            "numero_placa",
            "nombres",
            "apellidos",
            "estado_cuenta",
            "intentos_login_fallidos",
        ):
            if field in data:
                df.loc[mask, field] = data[field]
        if data.get("password"):
            df.loc[mask, "password_hash"] = hash_password(str(data["password"]))
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
