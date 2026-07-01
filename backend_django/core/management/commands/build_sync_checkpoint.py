"""Construye checkpoint + índice de IDs para ETL incremental rápido (una sola vez)."""

from django.core.management.base import BaseCommand, CommandError

from core.etl.sync_checkpoint import ensure_sync_state, load_checkpoint
from core.services.minio_store import MinioParquetStore


class Command(BaseCommand):
    help = "Inicializa checkpoint.json y synced_pb_ids.parquet desde fact_crimes consolidado."

    def handle(self, *args, **options):
        store = MinioParquetStore()
        if not store.has_consolidated_facts():
            raise CommandError("No hay fact_crimes consolidado en MinIO.")

        if load_checkpoint(store):
            self.stdout.write(self.style.WARNING("Checkpoint ya existe; reconstruyendo índice..."))

        self.stdout.write("Leyendo fact consolidado e indexando IDs (puede tardar ~1 min)...")
        existing_ids, max_id, fact_count, dim_max_ids, _ = ensure_sync_state(store)
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {len(existing_ids):,} IDs indexados, max_fact_id={max_id:,}, "
                f"fact_count={fact_count:,}, dims indexadas={len(dim_max_ids)}."
            )
        )
