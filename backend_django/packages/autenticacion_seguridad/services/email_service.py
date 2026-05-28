from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


def send_password_reset_code(*, to_email: str, code: str, nombre: str) -> None:
    subject = "CrimeTrack — Código de recuperación de contraseña"
    body = (
        f"Hola {nombre},\n\n"
        f"Recibimos una solicitud para restablecer tu contraseña en CrimeTrack Analytics.\n\n"
        f"Tu código de verificación es: {code}\n\n"
        f"Este código expira en 15 minutos. Si no solicitaste este cambio, ignora este mensaje.\n\n"
        f"— Equipo CrimeTrack Soporte\n"
        f"{getattr(settings, 'DEFAULT_FROM_EMAIL', '')}"
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=False,
    )


def send_backup_failure_alert(
    *,
    to_email: str,
    nombre: str,
    config_nombre: str,
    detalle: str,
) -> None:
    """HU-3: alerta a Comisario cuando falla un respaldo programado."""
    subject = "CrimeTrack — Fallo en respaldo programado"
    body = (
        f"Hola {nombre},\n\n"
        f"El respaldo programado «{config_nombre}» no se completó correctamente.\n\n"
        f"Detalle: {detalle}\n\n"
        f"Revise el módulo de respaldos y tome acciones correctivas.\n\n"
        f"— CrimeTrack Analytics Corp\n"
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=True,
    )
