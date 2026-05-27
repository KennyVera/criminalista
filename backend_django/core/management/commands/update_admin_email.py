"""
Actualiza el email del administrador (id_usuario=1) sin borrar el resto de tablas.
"""

from django.core.management.base import BaseCommand

from packages.autenticacion_seguridad.services.passwords import hash_password
from packages.autenticacion_seguridad.services.seed import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
)
from packages.shared.minio_transactional import TransactionalMinioStore


class Command(BaseCommand):
    help = "Cambia el email del admin a kennyvera43@gmail.com (y asegura tabla sesiones)"

    def handle(self, *args, **options):
        store = TransactionalMinioStore()
        store.ensure_tables()

        df = store.read_table("app_usuarios")
        if df.empty:
            self.stdout.write(
                self.style.WARNING("No hay usuarios. Ejecuta: python manage.py seed_auth_minio")
            )
            return

        mask = df["id_usuario"] == 1
        if not mask.any():
            mask = df.index == 0

        df.loc[mask, "email"] = DEFAULT_ADMIN_EMAIL
        df.loc[mask, "nombres"] = "Kenny"
        df.loc[mask, "apellidos"] = "Vera"
        df.loc[mask, "password_hash"] = hash_password(DEFAULT_ADMIN_PASSWORD)
        df.loc[mask, "estado_cuenta"] = "Activa"
        store.write_table("app_usuarios", df)

        self.stdout.write(self.style.SUCCESS(f"Admin actualizado: {DEFAULT_ADMIN_EMAIL}"))
        self.stdout.write(f"Contraseña: {DEFAULT_ADMIN_PASSWORD}")
