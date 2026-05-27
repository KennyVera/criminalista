"""
Generación de crimes_220k con distribución realista en el tiempo y dimensiones.

Objetivo: ~300k registros totales y gráficas de tendencias con datos en todos los años.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from core.services.faker_seed import (
    CHICAGO_CRIME_TYPES,
    DEFAULT_WORKERS,
    DISTRICTS,
    HISTORICAL_YEAR_WEIGHTS,
    HISTORICAL_YEARS,
    MAX_BATCH_SIZE,
    WARDS,
    _CRIME_TYPE_WEIGHTS,
    _DISTRICT_WEIGHTS,
    _create_one_isolated,
    _fake,
    _random_datetime_in_year,
    _unique_row_id,
)

YEAR_CHOICES = HISTORICAL_YEARS
YEAR_WEIGHTS = HISTORICAL_YEAR_WEIGHTS

ProgressCallback = Callable[[dict[str, Any]], None]


def gen_crimes_220k_for_year(fake, year: int) -> dict:
    """Registro crimes_220k con fecha anclada a un año concreto."""
    idx = random.choices(range(len(CHICAGO_CRIME_TYPES)), weights=_CRIME_TYPE_WEIGHTS, k=1)[0]
    primary, iucr, desc, fbi = CHICAGO_CRIME_TYPES[idx]
    dt = _random_datetime_in_year(year)
    lat = round(random.uniform(41.64, 42.02), 6)
    lon = round(random.uniform(-87.94, -87.52), 6)
    district = str(random.choices(DISTRICTS, weights=_DISTRICT_WEIGHTS, k=1)[0]).zfill(2)
    ward = str(random.choice(WARDS))
    beat = f"{district}{random.randint(10, 99)}"
    arrest_prob = 0.35 if year >= 2015 else 0.28
    return {
        "id": _unique_row_id(),
        "case_number": f"JK{random.randint(100000, 999999)}",
        "date": dt.strftime("%m/%d/%Y %I:%M:%S %p"),
        "block": fake.street_address(),
        "iucr": iucr,
        "primary_type": primary,
        "description": desc,
        "location_description": random.choice(
            ["STREET", "APARTMENT", "ALLEY", "PARKING LOT", "RESIDENCE", "SIDEWALK", "STORE"]
        ),
        "arrest": "true" if random.random() < arrest_prob else "false",
        "domestic": "true" if random.random() < 0.22 else "false",
        "beat": beat,
        "district": district,
        "ward": ward,
        "community_area": str(random.randint(1, 77)),
        "fbi_code": fbi,
        "year": str(year),
        "updated_on": dt.strftime("%m/%d/%Y %I:%M:%S %p"),
        "latitude": str(lat),
        "longitude": str(lon),
        "location": f"({lat}, {lon})",
    }


def _create_one_for_year(year: int) -> tuple[bool, dict | None, str | None]:
    body = gen_crimes_220k_for_year(_fake(), year)
    ok, record, err = _create_one_isolated("crimes_220k", body)
    if ok and record:
        return True, {**body, "pb_id": record.get("id"), "year": year}, None
    return ok, None, err


def bulk_insert_realistic_crimes(
    total_count: int,
    *,
    workers: int = DEFAULT_WORKERS,
    on_progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Inserta N registros con años distribuidos 2001–2026."""
    if total_count < 1:
        raise ValueError("total_count debe ser >= 1")

    years_plan = random.choices(YEAR_CHOICES, weights=YEAR_WEIGHTS, k=total_count)
    year_histogram: dict[int, int] = {}
    for y in years_plan:
        year_histogram[y] = year_histogram.get(y, 0) + 1

    workers = max(1, min(workers, 64, total_count))
    created = 0
    errors = 0
    samples: list[dict] = []
    error_messages: list[str] = []
    done = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_create_one_for_year, year) for year in years_plan]
        for fut in as_completed(futures):
            ok, payload, err = fut.result()
            done += 1
            if ok and payload:
                created += 1
                if len(samples) < 8:
                    samples.append(payload)
            else:
                errors += 1
                if err and len(error_messages) < 5 and err not in error_messages:
                    error_messages.append(err)

            if on_progress and (done % 100 == 0 or done == total_count):
                on_progress(
                    {
                        "done": done,
                        "total": total_count,
                        "created": created,
                        "errors": errors,
                        "percent": round(100 * done / total_count, 1),
                        "last_sample": samples[-1] if samples else None,
                    }
                )

    elapsed = round(time.time() - t0, 2)
    return {
        "success": created > 0,
        "partial": created > 0 and errors > 0,
        "created": created,
        "errors": errors,
        "requested": total_count,
        "elapsed_seconds": elapsed,
        "year_distribution": {str(k): v for k, v in sorted(year_histogram.items())},
        "samples": samples,
        "error_messages": error_messages,
        "message": (
            f"Se insertaron {created} registros realistas en crimes_220k "
            f"(distribuidos 2001–2026)."
        ),
        "hint_etl": "python manage.py etl_pb_to_minio",
    }


def run_realistic_seed_batch(
    count: int,
    *,
    workers: int = DEFAULT_WORKERS,
) -> dict[str, Any]:
    """Lote API (misma forma que run_faker_seed_batch)."""
    if count < 1:
        raise ValueError("La cantidad debe ser al menos 1")
    if count > MAX_BATCH_SIZE:
        raise ValueError(f"Máximo {MAX_BATCH_SIZE} registros por lote realista")

    result = bulk_insert_realistic_crimes(count, workers=workers)
    created = result["created"]
    errors = result["errors"]
    success = created > 0 and errors == 0
    partial = created > 0 and errors > 0

    return {
        "success": success or partial,
        "partial": partial,
        "realistic": True,
        "raw": {
            "requested": count,
            "created": created,
            "errors": errors,
            "elapsed_seconds": result["elapsed_seconds"],
            "year_distribution": result.get("year_distribution"),
        },
        "inserted_facts": created,
        "samples": result["samples"],
        "error_messages": result["error_messages"],
        "message": result["message"],
        "hint_etl": result["hint_etl"],
    }


def run_realistic_seed_100k(
    *,
    count: int = 100_000,
    workers: int = DEFAULT_WORKERS,
    on_progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Atajo: +100k hacia ~300k totales."""
    return bulk_insert_realistic_crimes(count, workers=workers, on_progress=on_progress)
