"""
Aplica reglas CORS en el bucket MinIO para Direct-to-Client (Presigned URLs + DuckDB-Wasm).
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from core.services.minio_cors import MinioCorsService, default_cors_origins


class Command(BaseCommand):
    help = (
        "Configura CORS en el bucket MinIO para permitir lectura directa desde React "
        "(Presigned URLs). Orígenes por defecto: CORS_ALLOWED_ORIGINS + localhost:5173."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--origins",
            nargs="+",
            default=None,
            help="Orígenes permitidos (ej. http://localhost:5173).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra la configuración sin aplicarla.",
        )
        parser.add_argument(
            "--show",
            action="store_true",
            help="Solo muestra la configuración CORS actual del bucket.",
        )

    def handle(self, *args, **options):
        service = MinioCorsService()

        if options["show"]:
            current = service.get_current_cors()
            if not current:
                self.stdout.write(self.style.WARNING("El bucket no tiene CORS configurado."))
                return
            self.stdout.write(self.style.SUCCESS("CORS actual:"))
            self.stdout.write(
                MinioCorsService.format_report(
                    {
                        "configuration": {"CORSRules": current},
                        "bucket": service.bucket,
                        "endpoint": service.store.endpoint,
                        "applied": False,
                    }
                )
            )
            return

        origins = options["origins"] or default_cors_origins()
        try:
            result = service.apply_cors(
                origins=origins,
                dry_run=options["dry_run"],
            )
        except Exception as exc:
            raise CommandError(f"No se pudo configurar CORS: {exc}") from exc

        if result.get("dry_run"):
            self.stdout.write(self.style.WARNING("Dry-run — no se aplicaron cambios."))
        else:
            method = result.get("apply_method", "boto3")
            self.stdout.write(
                self.style.SUCCESS(f"CORS aplicado correctamente (método: {method}).")
            )

        self.stdout.write(MinioCorsService.format_report(result))
        self.stdout.write("")
        self.stdout.write("Orígenes permitidos:")
        for origin in origins:
            self.stdout.write(f"  · {origin}")
