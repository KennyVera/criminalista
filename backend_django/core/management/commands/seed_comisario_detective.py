"""
Crea usuarios Comisario y Detective en MinIO sin borrar el admin existente.
"""

from django.core.management.base import BaseCommand

from packages.autenticacion_seguridad.services.seed import ensure_operational_users


class Command(BaseCommand):
    help = "Añade usuarios Comisario y Detective (credenciales de desarrollo)"

    def handle(self, *args, **options):
        result = ensure_operational_users()
        if result["created"]:
            self.stdout.write(
                self.style.SUCCESS(f"Creados: {', '.join(result['created'])}")
            )
        else:
            self.stdout.write("Comisario y Detective ya existían (sin cambios).")

        if result["skipped"]:
            self.stdout.write(f"Omitidos (ya registrados): {', '.join(result['skipped'])}")

        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Credenciales (desarrollo):"))
        for cred in result["credentials"]:
            self.stdout.write(f"  [{cred['rol']}]")
            self.stdout.write(f"    Email:    {cred['email']}")
            self.stdout.write(f"    Password: {cred['password']}")
            self.stdout.write(f"    Placa:    {cred['numero_placa']}")
            self.stdout.write("")
