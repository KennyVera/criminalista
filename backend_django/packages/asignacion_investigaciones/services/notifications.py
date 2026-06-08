from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


def send_assignment_notification(
    *,
    to_email: str,
    detective_nombre: str,
    case_number: str,
    comisario_nombre: str,
    fecha_asignacion: str,
) -> bool:
    """HU-3: notifica al detective cuando el Comisario le asigna un caso."""
    subject = f"CrimeTrack — Nuevo caso asignado ({case_number})"
    body = (
        f"Hola {detective_nombre},\n\n"
        f"El Comisario {comisario_nombre} le ha asignado el caso {case_number}.\n"
        f"Fecha de asignación: {fecha_asignacion}\n\n"
        f"Ingrese a CrimeTrack → Mis expedientes / Progreso de investigación "
        f"para revisar el expediente y registrar avances.\n\n"
        f"— CrimeTrack Analytics Corp\n"
    )
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False
