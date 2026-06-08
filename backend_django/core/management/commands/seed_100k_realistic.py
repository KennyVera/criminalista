"""Inserta 100k hechos con distribución histórica y opcionalmente ejecuta ETL a MinIO."""

from django.core.management.base import BaseCommand, CommandError

from core.services.faker_realistic import run_realistic_seed_100k


class Command(BaseCommand):
    help = (
        "Genera 100.000 registros adicionales en crimes_220k (años 2001–2026) "
        "para ~300k totales y gráficas de tendencias realistas. Luego ejecuta ETL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100_000,
            help="Cantidad de registros a insertar (default: 100000).",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=32,
            help="Hilos paralelos PocketBase (default: 32).",
        )
        parser.add_argument(
            "--skip-etl",
            action="store_true",
            help="Solo insertar en PocketBase, sin ETL a MinIO.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        workers = options["workers"]

        def progress(state: dict) -> None:
            pct = state.get("percent", 0)
            done = state.get("done", 0)
            total = state.get("total", count)
            self.stdout.write(
                f"\r  PocketBase: {done:,}/{total:,} ({pct}%)",
                ending="",
            )
            self.stdout.flush()

        self.stdout.write(self.style.WARNING(f"Insertando {count:,} registros realistas…"))
        try:
            from core.services.faker_realistic import resolve_gap_fill_weights

            gap = resolve_gap_fill_weights()
            self.stdout.write(
                f"  Gap-fill ({gap['source']}, meta ~{gap['target_year_volume']:,}): "
                f"{len(gap['sparse_years'])} años bajo meta"
            )
            top_gaps = sorted(
                gap.get("year_gaps_to_target", {}).items(),
                key=lambda x: int(x[1]),
                reverse=True,
            )[:8]
            if top_gaps:
                self.stdout.write(
                    "  Mayor déficit: "
                    + ", ".join(f"{y} (+{int(g):,})" for y, g in top_gaps)
                )
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  Gap-fill preview omitido: {exc}"))

        try:
            result = run_realistic_seed_100k(count=count, workers=workers, on_progress=progress)
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(result["message"]))
        if result.get("year_distribution"):
            self.stdout.write("Distribución por año (muestra):")
            for year, n in list(result["year_distribution"].items())[:8]:
                self.stdout.write(f"  · {year}: {n:,}")
            self.stdout.write("  · …")

        if options["skip_etl"]:
            self.stdout.write(
                self.style.WARNING("ETL omitido. Ejecuta: python manage.py etl_pb_to_minio")
            )
            return

        self.stdout.write(self.style.WARNING("Ejecutando ETL PocketBase -> MinIO..."))
        try:
            from core.etl.star_schema import run_etl_pb_to_minio

            etl = run_etl_pb_to_minio(export_raw_copy=True)
        except Exception as exc:
            raise CommandError(f"ETL falló: {exc}") from exc

        from core.services.analytics_service import invalidate_dashboard_cache

        invalidate_dashboard_cache()

        self.stdout.write(self.style.SUCCESS(etl["message"]))
        for name, rows in etl.get("collections", {}).items():
            self.stdout.write(f"  · {name}: {rows:,}")
