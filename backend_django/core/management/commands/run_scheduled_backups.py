"""Ejecuta respaldos programados vencidos (cron / Celery beat)."""

from django.core.management.base import BaseCommand

from packages.administracion_sistema.services.backups_admin import BackupsAdminService


class Command(BaseCommand):
    help = (
        "Ejecuta configuraciones de respaldo activas cuya hora programada ya venció. "
        "Programar vía Celery beat (cada minuto) o cron."
    )

    def handle(self, *args, **options):
        results = BackupsAdminService().run_due_scheduled()
        if not results:
            self.stdout.write("No hay respaldos programados vencidos.")
            return
        for item in results:
            estado = item.get("estado", "—")
            detalle = item.get("detalle", "")
            self.stdout.write(
                self.style.SUCCESS(f"Config #{item.get('config_id')}: {estado} — {detalle}")
                if item.get("success")
                else self.style.ERROR(f"Config #{item.get('config_id')}: {estado} — {detalle}")
            )
