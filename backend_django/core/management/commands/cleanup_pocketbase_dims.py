"""Elimina colecciones dim_* y fact_crimes de PocketBase (solo debe quedar crimes_220k)."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.services.minio_store import DIM_COLLECTIONS, MINIO_STAR_COLLECTIONS
from core.services.pocketbase import PocketBaseClient, PocketBaseError

KEEP = frozenset({"crimes_220k"})

# fact_crimes primero (referencia a dims); luego dimensiones; luego otras (prueba, etc.)
DELETE_ORDER = ["fact_crimes", *DIM_COLLECTIONS]


def _delete_priority(name: str) -> int:
    try:
        return DELETE_ORDER.index(name)
    except ValueError:
        return len(DELETE_ORDER)


class Command(BaseCommand):
    help = "Borra dimensiones y fact_crimes de PocketBase. Deja únicamente crimes_220k."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo lista colecciones que se eliminarían.",
        )

    def handle(self, *args, **options):
        if not settings.POCKETBASE_ADMIN_PASSWORD:
            raise CommandError("Define POCKETBASE_ADMIN_PASSWORD en .env")

        to_delete = set(MINIO_STAR_COLLECTIONS)

        with PocketBaseClient() as client:
            client.auth_admin()
            collections = client.list_collections()

            targets = []
            for col in collections:
                name = col.get("name", "")
                if name in KEEP or name.startswith("_"):
                    continue
                extra_drop = frozenset({"prueba"})
                if (
                    name in to_delete
                    or name.startswith("dim_")
                    or name == "fact_crimes"
                    or name in extra_drop
                ):
                    targets.append(col)

            targets.sort(key=lambda c: (_delete_priority(c["name"]), c["name"]))

            for col in targets:
                name = col["name"]
                if options["dry_run"]:
                    self.stdout.write(f"  [dry-run] eliminaría: {name}")
                    continue
                try:
                    client.delete_collection(col["id"])
                    self.stdout.write(self.style.WARNING(f"  - Eliminada: {name}"))
                except PocketBaseError as exc:
                    raise CommandError(f"No se pudo eliminar {name}: {exc}") from exc

        if options["dry_run"]:
            self.stdout.write(self.style.NOTICE("\nEjecuta sin --dry-run para aplicar."))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nPocketBase limpio. Solo permanece crimes_220k (+ colecciones de sistema).\n"
                )
            )
