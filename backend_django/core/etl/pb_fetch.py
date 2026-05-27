"""
Extraccion paralela de crimes_220k desde PocketBase.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from core.services.pocketbase import PocketBaseClient

FETCH_PER_PAGE = 500
FETCH_WORKERS = 8


def fetch_crimes_220k_parallel(
    pb: PocketBaseClient,
    *,
    per_page: int = FETCH_PER_PAGE,
    workers: int = FETCH_WORKERS,
) -> list[dict]:
    first = pb.list_records("crimes_220k", page=1, per_page=per_page, sort="@rowid")
    items: list[dict] = list(first.get("items", []))
    total_pages = int(first.get("totalPages", 1) or 1)
    if total_pages <= 1:
        return items

    token = pb.token
    base_url = pb.base_url

    def _page(page: int) -> list[dict]:
        with PocketBaseClient(base_url=base_url, token=token) as client:
            data = client.list_records(
                "crimes_220k", page=page, per_page=per_page, sort="@rowid"
            )
            return data.get("items", [])

    workers = max(1, min(workers, total_pages - 1, 16))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_page, p): p for p in range(2, total_pages + 1)}
        for fut in as_completed(futures):
            items.extend(fut.result())
    return items
