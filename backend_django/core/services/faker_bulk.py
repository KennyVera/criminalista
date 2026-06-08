"""
Inserción masiva en PocketBase por lotes de 5.000 (API /api/batches).
"""

from __future__ import annotations

from typing import Any, Callable

from core.services.faker_seed import BULK_INSERT_CHUNK, bulk_create_records


def bulk_insert_crimes_220k(
    total_count: int,
    *,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    workers: int | None = None,  # noqa: ARG001 — ignorado; se usa batch API
) -> dict[str, Any]:
    """Genera N registros Faker y los inserta en crimes_220k sin bloquear por hilo/registro."""
    del workers
    if total_count < 1:
        raise ValueError("total_count debe ser >= 1")

    result = bulk_create_records(
        "crimes_220k",
        total_count,
        on_progress=on_progress,
    )
    created = result["created"]
    errors = result["errors"]
    elapsed = result.get("elapsed_seconds", 0)

    return {
        "success": created > 0,
        "raw": {
            "requested": total_count,
            "created": created,
            "errors": errors,
            "elapsed_seconds": elapsed,
            "bulk_chunk_size": BULK_INSERT_CHUNK,
        },
        "inserted_facts": created,
        "samples": result.get("samples", []),
        "error_messages": result.get("error_messages", []),
        "message": f"Bulk insert: {created}/{total_count} registros en crimes_220k ({elapsed}s).",
    }
