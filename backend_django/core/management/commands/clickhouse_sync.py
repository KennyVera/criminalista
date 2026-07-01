"""
Sincroniza la capa analítica MinIO -> ClickHouse (crimetrack_analytics).

Crea el esquema si falta y recarga (full refresh) todas las tablas analíticas.
Es la misma lógica que orquesta Airflow; aquí se expone para bootstrap/verificación.

Uso:
    python manage.py clickhouse_sync
    python manage.py clickhouse_sync --schema-only
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from core.etl.clickhouse_loader import ensure_schema, load_all_to_clickhouse
from core.services.clickhouse_client import ClickHouseService


class Command(BaseCommand):
    help = "Carga las tablas analíticas de ClickHouse desde los Parquet de MinIO."

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema-only",
            action="store_true",
            help="Solo crea la base de datos y las tablas (sin cargar datos).",
        )

    def handle(self, *args, **options):
        if options["schema_only"]:
            ch = ClickHouseService()
            if not ch.ping():
                raise CommandError(
                    f"ClickHouse no responde en {ch.host}:{ch.port}. "
                    "Levanta: docker compose --profile analytics up -d"
                )
            ensure_schema(ch)
            self.stdout.write(self.style.SUCCESS("Esquema crimetrack_analytics asegurado."))
            return

        def progress(msg: str) -> None:
            self.stdout.write(f"  {msg}")

        try:
            results = load_all_to_clickhouse(on_progress=progress)
        except Exception as exc:  # noqa: BLE001
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Sincronización ClickHouse completada:"))
        for table, rows in results.items():
            self.stdout.write(f"  - {table}: {rows:,}".replace(",", "."))
