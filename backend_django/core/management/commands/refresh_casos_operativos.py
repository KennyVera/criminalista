"""Materializa app_casos_operativos desde dim_caso (DuckDB → Parquet transaccional)."""

from django.core.management.base import BaseCommand

from packages.asignacion_investigaciones.services.casos_operativos_store import (
    CasosOperativosStore,
)


class Command(BaseCommand):
    help = "Índice ligero de casos para asignaciones (evita leer 300k filas en cada pantalla)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limitar filas (pruebas); por defecto todos los casos",
        )

    def handle(self, *args, **options):
        result = CasosOperativosStore().refresh_materialized_index(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(result["message"]))
