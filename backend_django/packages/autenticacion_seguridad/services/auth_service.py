from __future__ import annotations

from typing import Any

import pandas as pd

from packages.autenticacion_seguridad.services.jwt_tokens import (
    create_access_token,
    decode_access_token,
    expiration_iso,
)
from packages.autenticacion_seguridad.services.passwords import verify_password
from packages.autenticacion_seguridad.services.security_policy import get_login_max_attempts
from packages.autenticacion_seguridad.services.session_service import (
    MOTIVO_ADMIN,
    MOTIVO_LOGOUT,
    SESSION_CLOSED_BY_ADMIN_MSG,
    SessionService,
)
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso


class AuthError(Exception):
    def __init__(self, message: str, *, code: str = "AUTH_ERROR"):
        super().__init__(message)
        self.code = code


_ACTIVE_STATES = frozenset({"activa", "active"})
_LOCKED_STATES = frozenset({"bloqueada", "blocked", "bloqueado"})


class AuthService:
    def __init__(self, store: TransactionalMinioStore | None = None) -> None:
        self.store = store or TransactionalMinioStore()
        self.sessions = SessionService(self.store)

    @staticmethod
    def _normalize_users_df(df: pd.DataFrame) -> pd.DataFrame:
        if "intentos_login_fallidos" not in df.columns:
            df = df.copy()
            df["intentos_login_fallidos"] = 0
        else:
            df = df.copy()
            df["intentos_login_fallidos"] = (
                pd.to_numeric(df["intentos_login_fallidos"], errors="coerce")
                .fillna(0)
                .astype(int)
            )
        return df

    def _read_users(self) -> pd.DataFrame:
        return self._normalize_users_df(self.store.read_table("app_usuarios"))

    def _account_state(self, user: dict) -> str:
        return str(user.get("estado_cuenta", "")).strip().lower()

    def _is_locked(self, user: dict) -> bool:
        return self._account_state(user) in _LOCKED_STATES

    def _is_active(self, user: dict) -> bool:
        return self._account_state(user) in _ACTIVE_STATES

    def _failed_attempts(self, user: dict) -> int:
        try:
            return int(user.get("intentos_login_fallidos") or 0)
        except (TypeError, ValueError):
            return 0

    def _set_user_auth_fields(self, user_id: int, **fields) -> None:
        df = self._read_users()
        mask = df["id_usuario"] == user_id
        if not mask.any():
            return
        for key, value in fields.items():
            if key in df.columns:
                df.loc[mask, key] = value
        self.store.write_table("app_usuarios", df)

    def _reset_failed_login(self, user_id: int) -> None:
        self._set_user_auth_fields(user_id, intentos_login_fallidos=0)

    def _record_failed_login(self, user_id: int) -> int:
        df = self._read_users()
        mask = df["id_usuario"] == user_id
        if not mask.any():
            return 0
        current = int(df.loc[mask, "intentos_login_fallidos"].iloc[0])
        new_count = current + 1
        df.loc[mask, "intentos_login_fallidos"] = new_count
        self.store.write_table("app_usuarios", df)
        return new_count

    def _lock_account(self, user_id: int) -> None:
        self._set_user_auth_fields(
            user_id,
            estado_cuenta="Bloqueada",
            intentos_login_fallidos=get_login_max_attempts(),
        )

    def _roles_map(self) -> dict[int, str]:
        df = self.store.read_table("app_roles")
        if df.empty:
            return {}
        return {
            int(r.id_rol): str(r.nombre_rol)
            for r in df.itertuples(index=False)
        }

    def list_roles(self) -> list[dict[str, Any]]:
        df = self.store.read_table("app_roles")
        return df.to_dict(orient="records")

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        df = self._read_users()
        if df.empty:
            return None
        mask = df["email"].astype(str).str.lower() == email.strip().lower()
        hits = df[mask]
        if hits.empty:
            return None
        return hits.iloc[0].to_dict()

    def login(
        self,
        email: str,
        password: str,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        max_attempts = get_login_max_attempts()
        user = self.get_user_by_email(email)
        if not user:
            self._audit(
                fk_usuario=None,
                accion="LOGIN_FAILED",
                detalle=f"Intento fallido: {email}",
                ip=ip,
            )
            raise AuthError("Credenciales inválidas")

        user_id = int(user["id_usuario"])

        if self._is_locked(user):
            raise AuthError(
                "Cuenta bloqueada por demasiados intentos fallidos. "
                "Contacte al administrador o recupere su contraseña.",
                code="ACCOUNT_LOCKED",
            )
        if not self._is_active(user):
            raise AuthError("Cuenta inactiva. Contacte al administrador.")

        if not verify_password(password, str(user["password_hash"])):
            failures = self._record_failed_login(user_id)
            self._audit(
                fk_usuario=user_id,
                accion="LOGIN_FAILED",
                detalle=f"Contraseña incorrecta ({failures}/{max_attempts})",
                ip=ip,
            )
            if failures >= max_attempts:
                self._lock_account(user_id)
                self._audit(
                    fk_usuario=user_id,
                    accion="ACCOUNT_LOCKED",
                    detalle=f"Cuenta bloqueada tras {max_attempts} intentos fallidos",
                    ip=ip,
                    tabla="app_usuarios",
                )
                raise AuthError(
                    f"Cuenta bloqueada tras {max_attempts} intentos fallidos. "
                    "Contacte al administrador o recupere su contraseña.",
                    code="ACCOUNT_LOCKED",
                )
            remaining = max_attempts - failures
            raise AuthError(
                f"Credenciales inválidas. Te quedan {remaining} intento(s) antes del bloqueo.",
                code="AUTH_FAILED",
            )

        self._reset_failed_login(user_id)

        roles = self._roles_map()
        fk_rol = int(user["fk_rol"])
        nombre_rol = roles.get(fk_rol, "Sin rol")
        jti = self.sessions.new_jti()
        exp_iso = expiration_iso()

        token = create_access_token(
            {
                "sub": str(user["id_usuario"]),
                "email": user["email"],
                "fk_rol": fk_rol,
                "nombre_rol": nombre_rol,
                "numero_placa": user["numero_placa"],
                "jti": jti,
            }
        )

        self.sessions.open_session(
            user=user,
            nombre_rol=nombre_rol,
            jti=jti,
            ip=ip,
            user_agent=user_agent,
            fecha_expiracion=exp_iso,
        )

        self._audit(
            fk_usuario=int(user["id_usuario"]),
            accion="LOGIN",
            detalle=f"Inicio de sesión: {user['email']}",
            ip=ip,
            tabla="app_sesiones_activas",
        )

        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": self._public_user(user, nombre_rol),
        }

    def logout(self, user_id: int, *, ip: str | None = None, jti: str | None = None) -> None:
        if jti:
            self.sessions.close_session(jti, motivo=MOTIVO_LOGOUT)
        self._audit(
            fk_usuario=user_id,
            accion="LOGOUT",
            detalle="Cierre de sesión",
            ip=ip,
            tabla="app_sesiones_activas",
        )

    def session_status_from_token(self, token: str) -> dict[str, Any]:
        try:
            payload = decode_access_token(token)
        except Exception as exc:
            raise AuthError(
                "Token inválido o expirado",
                code="SESSION_REVOKED",
            ) from exc
        jti = payload.get("jti")
        if not jti:
            raise AuthError(SESSION_CLOSED_BY_ADMIN_MSG, code="SESSION_REVOKED")
        return self.sessions.get_session_status(str(jti))

    def admin_close_session(self, id_sesion: int, *, admin_id: int, ip: str | None = None) -> dict:
        if not self.sessions.close_session_by_id(id_sesion, motivo=MOTIVO_ADMIN):
            raise AuthError("Sesión no encontrada o ya cerrada")
        self._audit(
            fk_usuario=admin_id,
            accion="SESSION_CLOSED_BY_ADMIN",
            detalle=f"Admin cerró sesión id={id_sesion}",
            ip=ip,
            tabla="app_sesiones_activas",
        )
        return {"message": "Sesión cerrada correctamente", "id_sesion": id_sesion}

    def me_from_token(self, token: str) -> dict[str, Any]:
        try:
            payload = decode_access_token(token)
        except Exception as exc:
            raise AuthError("Token inválido o expirado", code="SESSION_REVOKED") from exc

        jti = payload.get("jti")
        if not jti:
            raise AuthError(SESSION_CLOSED_BY_ADMIN_MSG, code="SESSION_REVOKED")
        status = self.sessions.get_session_status(str(jti))
        if not status.get("valid"):
            raise AuthError(
                status.get("message", SESSION_CLOSED_BY_ADMIN_MSG),
                code=status.get("code", "SESSION_REVOKED"),
            )

        self.sessions.touch_session(str(jti))

        user_id = int(payload["sub"])
        df = self._read_users()
        row = df[df["id_usuario"] == user_id]
        if row.empty:
            raise AuthError("Usuario no encontrado")
        user = row.iloc[0].to_dict()
        return self._public_user(user, payload.get("nombre_rol", ""))

    def list_active_sessions(self) -> list[dict[str, Any]]:
        return self.sessions.list_active_sessions()

    @staticmethod
    def _public_user(user: dict, nombre_rol: str) -> dict[str, Any]:
        return {
            "id_usuario": int(user["id_usuario"]),
            "fk_rol": int(user["fk_rol"]),
            "nombre_rol": nombre_rol,
            "numero_placa": user["numero_placa"],
            "nombres": user["nombres"],
            "apellidos": user["apellidos"],
            "email": user["email"],
            "estado_cuenta": user["estado_cuenta"],
        }

    def _audit(
        self,
        *,
        fk_usuario: int | None,
        accion: str,
        detalle: str,
        ip: str | None = None,
        tabla: str | None = None,
    ) -> None:
        self.store.append_row(
            "app_audit_logs",
            {
                "fk_usuario": fk_usuario,
                "accion": accion,
                "tabla_afectada": tabla or "",
                "detalle": detalle,
                "direccion_ip": ip or "",
                "fecha_hora": utc_now_iso(),
            },
        )
