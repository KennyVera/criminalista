"""Inserta N registros ÚNICOS en crimes_220k (solo PocketBase, sin ETL)."""

from django.core.management.base import BaseCommand, CommandError

from core.services.faker_unique import bulk_insert_unique_crimes


class Command(BaseCommand):
    help = (
        "Inserta registros nuevos y sin duplicados en crimes_220k (PocketBase). "
        "No ejecuta ETL a MinIO (solo PocketBase). Por defecto 200.000."
    )

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=200_000, help="Cantidad (default 200000).")
        parser.add_argument("--workers", type=int, default=32, help="Hilos paralelos (default 32).")
        parser.add_argument(
            "--no-prefill",
            action="store_true",
            help="No precargar claves existentes desde MinIO (más rápido, dedup solo en la corrida).",
        )
        parser.add_argument(
            "--no-gap-fill",
            action="store_true",
            help="No priorizar años/distritos con pocos datos (distribución histórica simple).",
        )

    def handle(self, *args, **options):
        count = options["count"]
        workers = options["workers"]

        def progress(state: dict) -> None:
            self.stdout.write(
                f"\r  PocketBase: {state.get('done', 0):,}/{state.get('total', count):,} "
                f"({state.get('percent', 0)}%) · creados={state.get('created', 0):,} "
                f"errores={state.get('errors', 0):,}",
                ending="",
            )
            self.stdout.flush()

        self.stdout.write(
            self.style.WARNING(f"Insertando {count:,} registros únicos en crimes_220k (solo PocketBase)…")
        )
        try:
            result = bulk_insert_unique_crimes(
                count,
                workers=workers,
                on_progress=progress,
                gap_fill=not options["no_gap_fill"],
                prefill_existing=not options["no_prefill"],
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write("")
        if result.get("prefilled_existing_keys"):
            self.stdout.write(
                f"  Claves existentes precargadas: {result['prefilled_existing_keys']:,}"
            )
        style = self.style.SUCCESS if not result["errors"] else self.style.WARNING
        self.stdout.write(style(result["message"]))
        self.stdout.write(f"  Tiempo: {result['elapsed_seconds']}s")
        if result.get("error_messages"):
            self.stdout.write(self.style.ERROR("  Errores (muestra):"))
            for msg in result["error_messages"]:
                self.stdout.write(f"    · {msg}")
        self.stdout.write(
            self.style.WARNING(
                "ETL omitido (solo PocketBase). Cuando quieras reflejarlo en MinIO/Dashboard: "
                "python manage.py etl_pb_to_minio"
            )
        )
