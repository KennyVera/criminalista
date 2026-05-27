"""
Insercion masiva en PocketBase por lotes (bulk chunks) con workers paralelos.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from core.services.faker_seed import (
    BULK_INSERT_CHUNK,
    DEFAULT_WORKERS,
    _bulk_create,
)


def bulk_insert_crimes_220k(
    total_count: int,
    *,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    workers: int = DEFAULT_WORKERS,
) -> dict[str, Any]:
    """
    Genera N registros Faker y los inserta en crimes_220k (lazy + paralelo).
    """
    if total_count < 1:
        raise ValueError("total_count debe ser >= 1")

    created = 0
    errors = 0
    samples: list[dict] = []
    error_messages: list[str] = []
    t0 = time.time()

    for offset in range(0, total_count, BULK_INSERT_CHUNK):
        chunk_size = min(BULK_INSERT_CHUNK, total_count - offset)

        def chunk_progress(state: dict[str, Any]) -> None:
            if not on_progress:
                return
            on_progress(
                {
                    "done": offset + state["done"],
                    "total": total_count,
                    "created": created + state["created"],
                    "errors": errors + state["errors"],
                    "percent": round(100 * (offset + state["done"]) / total_count, 1),
                    "last_sample": state.get("last_sample"),
                }
            )

        result = _bulk_create(
            "crimes_220k",
            [None] * chunk_size,
            workers=workers,
            on_progress=chunk_progress,
        )
        created += result["created"]
        errors += result["errors"]
        for s in result.get("samples", []):
            if len(samples) < 8:
                samples.append(s)
        for msg in result.get("error_messages", []):
            if len(error_messages) < 5 and msg not in error_messages:
                error_messages.append(msg)

    elapsed = round(time.time() - t0, 2)
    return {
        "success": created > 0,
        "raw": {
            "requested": total_count,
            "created": created,
            "errors": errors,
            "elapsed_seconds": elapsed,
            "bulk_chunk_size": BULK_INSERT_CHUNK,
            "workers": workers,
        },
        "inserted_facts": created,
        "samples": samples,
        "error_messages": error_messages,
        "message": f"Bulk insert: {created}/{total_count} registros en crimes_220k ({elapsed}s).",
    }
