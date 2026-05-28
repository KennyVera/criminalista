"""
Detección de pérdida de datos en MinIO y modo recuperación (CU-17).
"""

from __future__ import annotations

import os
from typing import Any

from django.conf import settings

from packages.administracion_sistema.services.backups_admin import BackupsAdminService
from packages.administracion_sistema.storage import AdminMinioStore
from packages.autenticacion_seguridad.services.jwt_tokens import create_access_token
from packages.shared.minio_transactional import TransactionalMinioStore, utc_now_iso


def recovery_credentials() -> tuple[str, str]:
    email = os.getenv(
        "CRIMETRACK_RECOVERY_EMAIL",
        getattr(settings, "CRIMETRACK_RECOVERY_EMAIL", "kennyvera43@gmail.com"),
    )
    password = os.getenv(
        "CRIMETRACK_RECOVERY_PASSWORD",
        getattr(settings, "CRIMETRACK_RECOVERY_PASSWORD", "CrimeTrack2026!"),
    )
    return email.strip().lower(), password


class RecoveryService:
    def check_status(self) -> dict[str, Any]:
        """Público: indica si el sistema requiere restauración desde respaldo."""
        minio_ok = True
        minio_error: str | None = None
        usuarios = 0
        roles = 0
        historial_count = 0

        try:
            tx = TransactionalMinioStore()
            users_df = tx.read_table("app_usuarios")
            roles_df = tx.read_table("app_roles")
            usuarios = int(len(users_df)) if users_df is not None else 0
            roles = int(len(roles_df)) if roles_df is not None else 0
        except Exception as exc:
            minio_ok = False
            minio_error = str(exc)
            usuarios = 0
            roles = 0

        try:
            admin = AdminMinioStore()
            hist = admin.read_table("sys_respaldos_historial")
            historial_count = int(len(hist)) if hist is not None else 0
        except Exception:
            historial_count = 0

        recovery_required = (not minio_ok) or usuarios < 1 or roles < 1
        if recovery_required:
            if not minio_ok:
                reason = "minio_inaccesible"
                message = (
                    "No se puede leer MinIO o faltan las tablas transaccionales. "
                    "Restaure un respaldo ZIP."
                )
            elif usuarios < 1:
                reason = "sin_usuarios"
                message = (
                    "No hay usuarios en el sistema (datos operativos eliminados o vacíos). "
                    "Un administrador debe restaurar un respaldo."
                )
            else:
                reason = "sin_roles"
                message = "Faltan roles del sistema. Restaure un respaldo completo."
        else:
            reason = None
            message = "Sistema operativo."

        return {
            "recovery_required": recovery_required,
            "reason": reason,
            "message": message,
            "minio_ok": minio_ok,
            "minio_error": minio_error,
            "usuarios": usuarios,
            "roles": roles,
            "historial_respaldos": historial_count,
            "timestamp": utc_now_iso(),
        }

    def recovery_login(self, email: str, password: str) -> dict[str, Any]:
        """Acceso de emergencia solo cuando recovery_required."""
        status = self.check_status()
        if not status["recovery_required"]:
            raise ValueError("El sistema no está en modo recuperación")

        expected_email, expected_password = recovery_credentials()
        if email.strip().lower() != expected_email or password != expected_password:
            raise ValueError("Credenciales de recuperación inválidas")

        token = create_access_token(
            {
                "sub": "0",
                "email": expected_email,
                "fk_rol": 1,
                "nombre_rol": "Admin",
                "recovery_mode": True,
                "numero_placa": "RECOVERY",
            }
        )
        return {
            "access_token": token,
            "token_type": "Bearer",
            "recovery_mode": True,
            "message": "Sesión de recuperación iniciada. Restaure el respaldo ZIP.",
        }

    def list_historial_recovery(self) -> list[dict[str, Any]]:
        try:
            return BackupsAdminService().list_history(limit=50)
        except Exception:
            return []

    def restore_zip(self, zip_bytes: bytes, *, operador: str) -> dict[str, Any]:
        return BackupsAdminService().restore_from_zip(zip_bytes, ejecutado_por=operador)
