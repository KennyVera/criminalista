from __future__ import annotations

import random
import string
from typing import Any

from django.core.cache import cache

from packages.autenticacion_seguridad.services.auth_service import AuthError, AuthService
from packages.autenticacion_seguridad.services.email_service import send_password_reset_code
from packages.autenticacion_seguridad.services.passwords import hash_password
from packages.autenticacion_seguridad.services.security_policy import (
    validate_password_strength,
)


class PasswordRecoveryService:
    TTL_SECONDS = 900  # 15 min
    CODE_LENGTH = 6

    def __init__(self) -> None:
        self.auth = AuthService()

    def _cache_key(self, email: str) -> str:
        return f"crimetrack:pwd_reset:{email.strip().lower()}"

    def _generate_code(self) -> str:
        return "".join(random.choices(string.digits, k=self.CODE_LENGTH))

    def request_code(self, email: str) -> dict[str, Any]:
        user = self.auth.get_user_by_email(email)
        if not user:
            # No revelar si el correo existe
            return {
                "message": "Si el correo está registrado, recibirás un código en unos minutos.",
                "sent": False,
            }
        estado = str(user.get("estado_cuenta", "")).lower()
        if estado not in ("activa", "active", "bloqueada", "blocked", "bloqueado"):
            raise AuthError("La cuenta no está activa. Contacte al administrador.")

        code = self._generate_code()
        cache.set(
            self._cache_key(email),
            {
                "code": code,
                "id_usuario": int(user["id_usuario"]),
            },
            self.TTL_SECONDS,
        )

        nombre = f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip() or "Usuario"
        send_password_reset_code(
            to_email=user["email"],
            code=code,
            nombre=nombre,
        )

        self.auth._audit(
            fk_usuario=int(user["id_usuario"]),
            accion="PASSWORD_RESET_REQUEST",
            detalle="Solicitud de recuperación de contraseña",
            tabla="app_usuarios",
        )

        return {
            "message": "Si el correo está registrado, recibirás un código en unos minutos.",
            "sent": True,
        }

    def reset_password(self, email: str, code: str, new_password: str) -> dict[str, Any]:
        try:
            validate_password_strength(new_password)
        except ValueError as exc:
            raise AuthError(str(exc)) from exc

        key = self._cache_key(email)
        payload = cache.get(key)
        if not payload:
            raise AuthError("Código expirado o inválido. Solicita uno nuevo.")

        if str(payload.get("code")) != str(code).strip():
            raise AuthError("Código incorrecto")

        user_id = int(payload["id_usuario"])
        df = self.auth._read_users()
        mask = df["id_usuario"] == user_id
        if not mask.any():
            raise AuthError("Usuario no encontrado")

        df.loc[mask, "password_hash"] = hash_password(new_password)
        df.loc[mask, "estado_cuenta"] = "Activa"
        if "intentos_login_fallidos" in df.columns:
            df.loc[mask, "intentos_login_fallidos"] = 0
        else:
            df["intentos_login_fallidos"] = 0
            df.loc[mask, "intentos_login_fallidos"] = 0
        self.auth.store.write_table("app_usuarios", df)
        cache.delete(key)

        self.auth._audit(
            fk_usuario=user_id,
            accion="PASSWORD_RESET_OK",
            detalle="Contraseña actualizada vía recuperación",
            tabla="app_usuarios",
        )

        return {"message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}
