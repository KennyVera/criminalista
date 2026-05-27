"""
Crea tablas transaccionales RBAC en MinIO y usuario administrador inicial.
"""

from django.core.management.base import BaseCommand

from packages.autenticacion_seguridad.services.seed import seed_auth_data


class Command(BaseCommand):
    help = "Semilla: app_roles, app_usuarios y tablas transaccionales en MinIO"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-reset",
            action="store_true",
            help="No vaciar tablas existentes antes de sembrar roles/usuario",
        )

    def handle(self, *args, **options):
        result = seed_auth_data(reset=not options["no_reset"])
        self.stdout.write(self.style.SUCCESS("Tablas transaccionales en MinIO listas."))
        self.stdout.write(f"  Prefijo: {result['minio_prefix']}")
        for t in result["tables"]:
            self.stdout.write(f"  - {t}.parquet")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Credenciales de acceso:"))
        self.stdout.write(f"  Email:    {result['email']}")
        self.stdout.write(f"  Password: {result['password']}")
        self.stdout.write(f"  Placa:    {result['numero_placa']}")
