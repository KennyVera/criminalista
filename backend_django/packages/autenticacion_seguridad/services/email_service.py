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
