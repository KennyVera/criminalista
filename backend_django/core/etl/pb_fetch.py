"""
Extracción crimes_220k desde PocketBase — skipTotal=1 + paginación cursor (memoria plana).
"""

from __future__ import annotations

import gc
from collections.abc import Generator, Iterator
from typing import Any, Callable

import pandas as pd

from core.services.pocketbase import PocketBaseClient

FETCH_PER_PAGE = int(__import__("os").getenv("ETL_PB_PER_PAGE", "500"))
FETCH_WORKERS = 8


def iter_crimes_220k_chunks(
    pb: PocketBaseClient,
    *,
    per_page: int = FETCH_PER_PAGE,
    sort: str = "@rowid",
) -> Iterator[list[dict[str, Any]]]:
    """
    Generador de páginas sin COUNT en SQLite (skipTotal=1).
    Termina cuando una página devuelve menos registros que per_page.
    """
    page = 1
    while True:
        data = pb.list_records(
            "crimes_220k",
            page=page,
            per_page=per_page,
            sort=sort,
            skip_total=True,
        )
        batch = list(data.get("items", []))
        if not batch:
            break
        yield batch
        if len(batch) < per_page:
            break
        page += 1


def iter_crimes_220k_records(
    pb: PocketBaseClient,
    *,
    per_page: int = FETCH_PER_PAGE,
) -> Generator[dict[str, Any], None, None]:
    """Yield registro a registro — uso mínimo de memoria en el worker Celery."""
    for chunk in iter_crimes_220k_chunks(pb, per_page=per_page):
        yield from chunk


def fetch_crimes_220k_streaming(
    pb: PocketBaseClient,
    *,
    per_page: int = FETCH_PER_PAGE,
    on_chunk: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Acumula chunks con skipTotal=1. Reporta progreso por página sin totalItems.
    """
    items: list[dict[str, Any]] = []
    page = 0
    for chunk in iter_crimes_220k_chunks(pb, per_page=per_page):
        page += 1
        items.extend(chunk)
        if on_chunk:
            on_chunk(
                {
                    "page": page,
                    "chunk_rows": len(chunk),
                    "accumulated": len(items),
                    "per_page": per_page,
                }
            )
        if page % 20 == 0:
            gc.collect()
    return items


def fetch_crimes_220k_parallel(
    pb: PocketBaseClient,
    *,
    per_page: int = FETCH_PER_PAGE,
    workers: int = FETCH_WORKERS,
) -> list[dict[str, Any]]:
    """
    Extracción secuencial optimizada (skipTotal=1).
    El nombre se conserva por compatibilidad con star_schema / Celery.
    """
    del workers  # paralelo incompatible con skipTotal sin COUNT

    def _progress(state: dict[str, Any]) -> None:
        pass

    return fetch_crimes_220k_streaming(pb, per_page=per_page, on_chunk=_progress)


def crimes_220k_to_dataframe(
    pb: PocketBaseClient,
    *,
    per_page: int = FETCH_PER_PAGE,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> pd.DataFrame:
    """Construye DataFrame desde chunks — evita list() monolítica intermedia."""
    frames: list[pd.DataFrame] = []
    total = 0
    page = 0

    for chunk in iter_crimes_220k_chunks(pb, per_page=per_page):
        page += 1
        total += len(chunk)
        if chunk:
            frames.append(pd.DataFrame(chunk))
        if on_progress:
            pct = min(24, int(page * 2))
            on_progress(
                {
                    "phase": "extract",
                    "percent": pct,
                    "message": f"Extrayendo página {page} ({total:,} filas)...".replace(",", "."),
                    "page": page,
                    "accumulated": total,
                }
            )

    if not frames:
        return pd.DataFrame()

    raw_df = pd.concat(frames, ignore_index=True)
    del frames
    gc.collect()
    return raw_df.drop(
        columns=[c for c in raw_df.columns if c in ("collectionId", "collectionName", "expand")],
        errors="ignore",
    )
