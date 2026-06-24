"""ETL incremental: agrega solo los registros nuevos de crimes_220k a MinIO (sin reconstruir todo)."""

from django.core.management.base import BaseCommand, CommandError

from core.etl.incremental_etl import run_incremental_etl


class Command(BaseCommand):
    help = (
        "Detecta los registros de crimes_220k que aún no están en el modelo estrella "
        "de MinIO y los anexa (dimensiones + fact consolidado) sin reconstruir todo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-page",
            type=int,
            default=500,
            help="Tamaño de página al leer PocketBase (default 500).",
        )

    def handle(self, *args, **options):
        def progress(state: dict) -> None:
            msg = state.get("message")
            if msg:
                self.stdout.write(f"  · {msg}")

        self.stdout.write(self.style.WARNING("ETL incremental PocketBase → MinIO (solo nuevos)…"))
        try:
            result = run_incremental_etl(per_page=options["per_page"], on_progress=progress)
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(result["message"]))
        if result.get("new_records"):
            self.stdout.write(f"  Registros nuevos: {result['new_records']:,}")
            self.stdout.write(
                f"  fact_crimes: {result['fact_before']:,} → {result['fact_after']:,}"
            )
            self.stdout.write("  Dimensiones (nuevos / total):")
            for name, info in result.get("dimensions", {}).items():
                self.stdout.write(f"    · {name}: +{info['new']:,} / {info['total']:,}")
        self.stdout.write(f"  Tiempo: {result['elapsed_seconds']}s")
