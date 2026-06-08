"""
Generación de datos aleatorios en crimes_220k (PocketBase — dataset crudo).
El modelo estrella (dims + fact) se materializa en MinIO vía etl_pb_to_minio.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Callable

from django.utils import timezone

from core.pocketbase.schema import FACT_RELATION_NAMES
from core.services.pocketbase import PocketBaseClient, PocketBaseError

try:
    from faker import Faker
except ImportError:
    Faker = None  # type: ignore

MIN_DIM_RECORDS = 20
SAMPLE_IDS_PER_DIM = 400
MAX_FACTS_PER_REQUEST = 500_000
MAX_BATCH_SIZE = 5000
BULK_INSERT_CHUNK = 5000
PB_API_BATCH_SIZE = 100
DEFAULT_WORKERS = 32

CHICAGO_CRIME_TYPES = [
    ("THEFT", "06", "Theft over $500", "theft"),
    ("BATTERY", "08A", "Simple battery", "assault"),
    ("ASSAULT", "08B", "Aggravated assault", "assault"),
    ("BURGLARY", "05", "Unlawful entry", "burglary"),
    ("CRIMINAL DAMAGE", "14A", "Property damage", "vandalism"),
    ("NARCOTICS", "18", "Possession controlled substance", "drugs"),
    ("ROBBERY", "03", "Strongarm robbery", "robbery"),
    ("MOTOR VEHICLE THEFT", "07", "Vehicle theft", "theft"),
]

DISTRICTS = list(range(1, 26))
WARDS = list(range(1, 51))

# Distribución histórica 2001–2026 (más volumen en años recientes)
HISTORICAL_YEARS = list(range(2001, 2027))
HISTORICAL_YEAR_WEIGHTS = [
    1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45,
    1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.85, 1.95, 2.1, 2.25,
    2.4, 2.55, 2.7, 2.85, 3.0, 3.2,
]
_CRIME_TYPE_WEIGHTS = [22, 18, 12, 10, 10, 8, 8, 12]
_DISTRICT_WEIGHTS = [
    6, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
]
TURNOS = ["Mañana", "Tarde", "Noche", "Madrugada"]
ESTADOS_CASO = ["Abierto", "En investigación", "Cerrado", "Archivado"]
PRIORIDADES = ["Baja", "Media", "Alta", "Crítica"]

ProgressCallback = Callable[[dict[str, Any]], None]


def _fake() -> Faker:
    if Faker is None:
        raise RuntimeError("Instala Faker: pip install Faker")
    return Faker("en_US")


def _iso_date_between(fake: Faker, days_back: int = 365) -> str:
    dt = fake.date_time_between(
        start_date=f"-{days_back}d",
        end_date="now",
        tzinfo=timezone.get_current_timezone(),
    )
    return dt.strftime("%Y-%m-%d %H:%M:%S.000Z")


def _legacy_id() -> int:
    return random.randint(900_000_000, 999_999_999)


def _unique_row_id() -> str:
    """Campo text `id` obligatorio en crimes_220k (ID legado / negocio)."""
    return str(random.randint(1_000_000_000, 9_999_999_999))


def _random_datetime_in_year(year: int) -> datetime:
    tz = timezone.get_current_timezone()
    start = datetime(year, 1, 1, tzinfo=tz)
    end = datetime(year, 12, 31, 23, 59, 59, tzinfo=tz)
    now = datetime.now(tz=tz)
    if year >= now.year:
        end = min(end, now)
    delta = end - start
    seconds = random.randint(0, max(1, int(delta.total_seconds())))
    return start + timedelta(seconds=seconds)


def _gen_crimes_220k(fake: Faker) -> dict:
    """Registro plano compatible con crimes_220k (origen ETL)."""
    idx = random.choices(range(len(CHICAGO_CRIME_TYPES)), weights=_CRIME_TYPE_WEIGHTS, k=1)[0]
    primary, iucr, desc, fbi = CHICAGO_CRIME_TYPES[idx]
    year = random.choices(HISTORICAL_YEARS, weights=HISTORICAL_YEAR_WEIGHTS, k=1)[0]
    dt = _random_datetime_in_year(year)
    lat = round(random.uniform(41.64, 42.02), 6)
    lon = round(random.uniform(-87.94, -87.52), 6)
    district = str(random.choices(DISTRICTS, weights=_DISTRICT_WEIGHTS, k=1)[0]).zfill(2)
    ward = str(random.choice(WARDS))
    beat = f"{district}{random.randint(10, 99)}"
    return {
        "id": _unique_row_id(),
        "case_number": f"JK{random.randint(100000, 999999)}",
        "date": dt.strftime("%m/%d/%Y %I:%M:%S %p"),
        "block": fake.street_address(),
        "iucr": iucr,
        "primary_type": primary,
        "description": desc,
        "location_description": random.choice(
            ["STREET", "APARTMENT", "ALLEY", "PARKING LOT", "RESIDENCE", "SIDEWALK"]
        ),
        "arrest": random.choice(["true", "false"]),
        "domestic": random.choice(["true", "false"]),
        "beat": beat,
        "district": district,
        "ward": ward,
        "community_area": str(random.randint(1, 77)),
        "fbi_code": fbi,
        "year": str(dt.year),
        "updated_on": dt.strftime("%m/%d/%Y %I:%M:%S %p"),
        "latitude": str(lat),
        "longitude": str(lon),
        "location": f"({lat}, {lon})",
    }


def _create_one_isolated(collection: str, body: dict) -> tuple[bool, dict | None, str | None]:
    """Un cliente HTTP por hilo (httpx no es thread-safe)."""
    try:
        with PocketBaseClient() as pb:
            pb.auth_admin()
            record = pb.create_record(collection, body)
            return True, record, None
    except PocketBaseError as exc:
        return False, None, str(exc)


def _create_one_generated(collection: str) -> tuple[bool, dict | None, str | None]:
    """Genera el body en el worker (menos RAM con 100k+ registros)."""
    body = _gen_crimes_220k(_fake())
    ok, record, err = _create_one_isolated(collection, body)
    if ok and record:
        return True, {**body, "pb_id": record.get("id")}, None
    return ok, None, err


def bulk_create_records(
    collection: str,
    count: int,
    *,
    body_factory: Callable[[], dict] | None = None,
    on_progress: ProgressCallback | None = None,
    workers: int = DEFAULT_WORKERS,
) -> dict[str, Any]:
    """
    Genera e inserta en chunks de BULK_INSERT_CHUNK (inserción paralela por registro).
    Compatible con PocketBase sin endpoint /api/batches (imagen muchobien).
    """
    if count < 1:
        raise ValueError("count debe ser >= 1")

    factory = body_factory or (lambda: _gen_crimes_220k(_fake()))
    created = 0
    errors = 0
    samples: list[dict] = []
    error_messages: list[str] = []
    t0 = time.time()

    for offset in range(0, count, BULK_INSERT_CHUNK):
        chunk_n = min(BULK_INSERT_CHUNK, count - offset)
        bodies = [factory() for _ in range(chunk_n)]

        def chunk_progress(state: dict[str, Any]) -> None:
            if not on_progress:
                return
            on_progress(
                {
                    "done": offset + state["done"],
                    "total": count,
                    "created": created + state["created"],
                    "errors": errors + state["errors"],
                    "percent": round(100 * (offset + state["done"]) / count, 1),
                    "last_sample": state.get("last_sample"),
                }
            )

        result = _bulk_create(
            collection,
            bodies,
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
        "created": created,
        "errors": errors,
        "samples": samples,
        "error_messages": error_messages,
        "elapsed_seconds": elapsed,
    }


def _bulk_create(
    collection: str,
    bodies: list[dict | None],
    *,
    workers: int = DEFAULT_WORKERS,
    on_progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    if not bodies:
        return {
            "created": 0,
            "errors": 0,
            "samples": [],
            "error_messages": [],
        }

    lazy = bodies[0] is None
    total = len(bodies)
    workers = max(1, min(workers, 64, total))
    created = 0
    errors = 0
    samples: list[dict] = []
    error_messages: list[str] = []
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        if lazy:
            futures = [pool.submit(_create_one_generated, collection) for _ in range(total)]
        else:
            futures = [
                pool.submit(_create_one_isolated, collection, b)
                for b in bodies
                if b is not None
            ]

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

            if on_progress and (done % 50 == 0 or done == total):
                on_progress(
                    {
                        "done": done,
                        "total": total,
                        "created": created,
                        "errors": errors,
                        "percent": round(100 * done / total, 1),
                        "last_sample": samples[-1] if samples else None,
                        "last_error": err,
                    }
                )

    return {
        "created": created,
        "errors": errors,
        "samples": samples,
        "error_messages": error_messages,
    }


def run_faker_seed_batch(
    count: int,
    *,
    workers: int = DEFAULT_WORKERS,
) -> dict[str, Any]:
    """Inserta hasta MAX_BATCH_SIZE registros en crimes_220k."""
    if count < 1:
        raise ValueError("La cantidad debe ser al menos 1")
    if count > MAX_BATCH_SIZE:
        raise ValueError(f"Máximo {MAX_BATCH_SIZE} registros por lote")

    t0 = time.time()
    result = bulk_create_records("crimes_220k", count)
    elapsed = round(time.time() - t0, 2)

    created = result["created"]
    errors = result["errors"]
    success = created > 0 and errors == 0
    partial = created > 0 and errors > 0

    if created == 0:
        message = (
            "No se insertó ningún registro. "
            f"Error: {result['error_messages'][0] if result['error_messages'] else 'desconocido'}"
        )
    elif partial:
        message = f"Se insertaron {created} de {count} registros ({errors} errores)."
    else:
        message = f"Se insertaron {created} registros en crimes_220k (PocketBase)."

    return {
        "success": success or partial,
        "partial": partial,
        "raw": {
            "requested": count,
            "created": created,
            "errors": errors,
            "elapsed_seconds": elapsed,
        },
        "inserted_facts": created,
        "samples": result["samples"],
        "error_messages": result["error_messages"],
        "message": message,
        "hint_etl": "python manage.py etl_pb_to_minio",
    }


def run_faker_seed(
    raw_count: int,
    *,
    workers: int = DEFAULT_WORKERS,
    on_progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Inserta N filas crudas en crimes_220k (lotes internos)."""
    if raw_count < 1:
        raise ValueError("La cantidad debe ser al menos 1")
    if raw_count > MAX_FACTS_PER_REQUEST:
        raise ValueError(f"Máximo {MAX_FACTS_PER_REQUEST} registros por solicitud")

    t0 = time.time()
    result = bulk_create_records(
        "crimes_220k",
        raw_count,
        on_progress=on_progress,
    )
    elapsed = round(time.time() - t0, 2)

    created = result["created"]
    errors = result["errors"]

    return {
        "success": created > 0,
        "partial": created > 0 and errors > 0,
        "raw": {
            "requested": raw_count,
            "created": created,
            "errors": errors,
            "elapsed_seconds": elapsed,
        },
        "inserted_facts": created,
        "samples": result["samples"],
        "error_messages": result["error_messages"],
        "message": (
            f"Se insertaron {created} de {raw_count} registros en crimes_220k."
            if errors
            else f"Se insertaron {created} registros en crimes_220k (PocketBase)."
        ),
        "hint_etl": "python manage.py etl_pb_to_minio",
    }
