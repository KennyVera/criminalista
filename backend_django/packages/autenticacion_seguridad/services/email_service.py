from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMessage, send_mail


def send_report_email(
    *,
    to_emails: list[str],
    subject: str,
    body: str,
    pdf_bytes: bytes,
    filename: str,
) -> None:
    """Envía un reporte PDF como adjunto a uno o varios destinatarios (CU-O40)."""
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[e for e in to_emails if e],
    )
    msg.attach(filename, pdf_bytes, "application/pdf")
    msg.send(fail_silently=False)


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


def send_login_mfa_code(*, to_email: str, code: str, nombre: str, minutes: int = 5) -> None:
    """Envía el código de verificación de segundo factor (2FA) para el inicio de sesión."""
    subject = "CrimeTrack — Código de verificación de inicio de sesión"
    body = (
        f"Hola {nombre},\n\n"
        f"Detectamos un inicio de sesión en tu cuenta de administrador en CrimeTrack Analytics.\n\n"
        f"Tu código de verificación es: {code}\n\n"
        f"Ingresa este código para completar el acceso. Expira en {minutes} minutos.\n"
        f"Si no fuiste tú, cambia tu contraseña de inmediato.\n\n"
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


def send_new_user_credentials(
    *,
    to_email: str,
    nombre: str,
    password: str,
    numero_placa: str,
    nombre_rol: str,
    login_url: str,
) -> None:
    """Envía credenciales de acceso al usuario recién registrado por un administrador."""
    subject = "CrimeTrack — Acceso a tu cuenta"
    body = (
        f"Hola {nombre},\n\n"
        f"Un administrador creó tu cuenta en CrimeTrack Analytics.\n\n"
        f"Rol asignado: {nombre_rol}\n"
        f"Número de placa: {numero_placa}\n"
        f"Correo de acceso: {to_email}\n"
        f"Contraseña temporal: {password}\n\n"
        f"Ingresa en: {login_url}\n\n"
        f"Por seguridad, cambia tu contraseña después del primer inicio de sesión.\n\n"
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
