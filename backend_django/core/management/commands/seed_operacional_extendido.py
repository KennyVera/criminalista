"""Asegura tablas operativas nuevas (permisos + estructura policial) sin borrar datos."""

from django.core.management.base import BaseCommand

from packages.autenticacion_seguridad.services.permisos_operativos_service import (
    PermisosOperativosService,
)
from packages.estructura_policial.services.seed import seed_estructura_policial
from packages.shared.minio_transactional import TransactionalMinioStore


class Command(BaseCommand):
    help = "Crea/actualiza app_permisos, estructura policial y tablas operativas nuevas en MinIO."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-org",
            action="store_true",
            help="Recrea departamentos, distritos, estaciones y personal demo.",
        )

    def handle(self, *args, **options):
        store = TransactionalMinioStore()
        store.ensure_tables()
        perm = PermisosOperativosService(store).seed_defaults(reset_relations=False)
        org = seed_estructura_policial(store, reset=options["reset_org"])
        self.stdout.write(self.style.SUCCESS(f"Permisos: {perm}"))
        self.stdout.write(self.style.SUCCESS(f"Estructura policial: {org}"))
