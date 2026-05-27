from django.core.management.base import BaseCommand

from packages.administracion_sistema.services.seed import seed_admin_tables


class Command(BaseCommand):
    help = "Semilla tablas admin en MinIO (permisos, políticas, catálogos, zonas...)"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Vaciar tablas admin antes")

    def handle(self, *args, **options):
        result = seed_admin_tables(reset=options["reset"])
        self.stdout.write(self.style.SUCCESS("Administración del sistema — tablas MinIO listas."))
        for t in result["tables"]:
            self.stdout.write(f"  - datasets/admin/{t}.parquet")
