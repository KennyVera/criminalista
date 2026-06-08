"""Actualiza la tabla materializada app_dashboard_summary (cron / post-ETL)."""

from django.core.management.base import BaseCommand

from packages.dashboard_analitica.services.summary_materializer import (
    materialize_dashboard_summary,
)


class Command(BaseCommand):
    help = (
        "Precalcula métricas del dashboard en app_dashboard_summary (MinIO transaccional). "
        "Programar vía Celery beat o cron cada 15-60 min y tras cada ETL."
    )

    def handle(self, *args, **options):
        self.stdout.write("Materializando resumen del dashboard (DuckDB → app_dashboard_summary)...")
        result = materialize_dashboard_summary()
        if result.get("success"):
            self.stdout.write(self.style.SUCCESS(result["message"]))
        else:
            self.stdout.write(self.style.ERROR(str(result)))
