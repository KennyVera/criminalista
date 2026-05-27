"""ETL: PocketBase (crimes_220k) → Parquet → MinIO (modelo estrella)."""

from django.core.management.base import BaseCommand, CommandError

from core.etl.star_schema import run_etl_pb_to_minio


class Command(BaseCommand):
    help = (
        "Extrae crimes_220k desde PocketBase, transforma a modelo estrella "
        "y carga Parquet en MinIO (requisitos académicos 1–3)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-raw-copy",
            action="store_true",
            help="No guardar copia crimes_220k.parquet en MinIO (solo dims + fact).",
        )

    def handle(self, *args, **options):
        try:
            result = run_etl_pb_to_minio(export_raw_copy=not options["no_raw_copy"])
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(result["message"]))
        for name, count in result.get("collections", {}).items():
            self.stdout.write(f"  · {name}: {count:,} filas en MinIO")
