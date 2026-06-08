"""
Generación de crimes_220k con distribución realista en el tiempo y dimensiones.

Objetivo: ~300k registros totales y gráficas de tendencias con datos en todos los años.
Prioriza años y distritos con pocos o ningún registro (gap-fill).
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable

from core.services.faker_seed import (
    BULK_INSERT_CHUNK,
    CHICAGO_CRIME_TYPES,
    DEFAULT_WORKERS,
    DISTRICTS,
    HISTORICAL_YEAR_WEIGHTS,
    HISTORICAL_YEARS,
    MAX_BATCH_SIZE,
    WARDS,
    _CRIME_TYPE_WEIGHTS,
    _DISTRICT_WEIGHTS,
    _bulk_create,
    _fake,
    _random_datetime_in_year,
    _unique_row_id,
)

logger = logging.getLogger(__name__)

YEAR_CHOICES = HISTORICAL_YEARS
YEAR_WEIGHTS = HISTORICAL_YEAR_WEIGHTS
TARGET_YEAR_VOLUME = 80_000

ProgressCallback = Callable[[dict[str, Any]], None]


def _inverse_frequency_weights(keys: list, counts: dict) -> list[float]:
    """Más peso a buckets con menos datos (años/distritos vacíos primero)."""
    max_c = max(counts.values()) if counts else 0
    return [(max_c + 100) / (counts.get(k, 0) + 1) for k in keys]


def _target_year_weights(
    years: list[int],
    counts: dict[int, int],
    *,
    target: int = TARGET_YEAR_VOLUME,
) -> list[float]:
    """Prioriza años lejos del objetivo (~80k) para equilibrar la tendencia."""
    weights: list[float] = []
    for y in years:
        gap = max(0, target - counts.get(y, 0))
        weights.append(float(gap))
    if not any(w > 0 for w in weights):
        return _inverse_frequency_weights(years, counts)
    return weights


def _year_district_counts_duckdb() -> tuple[dict[int, int], dict[int, int]] | None:
    """Histogramas desde Parquet en MinIO (rápido, sin paginar PocketBase)."""
    try:
        from core.services.analytics_service import AnalyticsService
        from core.services.minio_store import MinioParquetStore

        store = MinioParquetStore()
        analytics = AnalyticsService(store)
        con = analytics.connection()
        raw_key = store._object_key("crimes_220k")
        src = analytics._s3_uri(raw_key)
        try:
            con.execute(f"SELECT 1 FROM read_parquet('{src}') LIMIT 1").fetchone()
        except Exception:
            return None

        year_rows = con.execute(
            f"""
            SELECT CAST(year AS INTEGER) AS y, COUNT(*)::BIGINT AS c
            FROM read_parquet('{src}')
            WHERE year IS NOT NULL AND TRIM(CAST(year AS VARCHAR)) != ''
            GROUP BY 1
            """
        ).fetchall()
        dist_rows = con.execute(
            f"""
            SELECT CAST(district AS INTEGER) AS d, COUNT(*)::BIGINT AS c
            FROM read_parquet('{src}')
            WHERE district IS NOT NULL AND TRIM(CAST(district AS VARCHAR)) != ''
            GROUP BY 1
            """
        ).fetchall()
        year_counts = {int(r[0]): int(r[1]) for r in year_rows}
        dist_counts = {int(r[0]): int(r[1]) for r in dist_rows}
        return year_counts, dist_counts
    except Exception as exc:
        logger.debug("gap-fill DuckDB no disponible: %s", exc)
        return None


def _year_district_counts_pocketbase() -> tuple[dict[int, int], dict[int, int]]:
    """Conteos por filtro PB (26 años + 25 distritos, peticiones ligeras)."""
    from core.services.pocketbase import PocketBaseClient

    year_counts: dict[int, int] = {y: 0 for y in HISTORICAL_YEARS}
    dist_counts: dict[int, int] = {d: 0 for d in DISTRICTS}
    with PocketBaseClient() as pb:
        pb.auth_admin()
        for year in HISTORICAL_YEARS:
            year_counts[year] = pb.count_records(
                "crimes_220k", filter_query=f'year="{year}"'
            )
        for district in DISTRICTS:
            ds = str(district).zfill(2)
            dist_counts[district] = pb.count_records(
                "crimes_220k", filter_query=f'district="{ds}"'
            )
    return year_counts, dist_counts


def resolve_gap_fill_weights() -> dict[str, Any]:
    """
    Calcula pesos de muestreo inversamente proporcionales al volumen existente.
    Años/distritos sin datos reciben el mayor peso.
    """
    histograms = _year_district_counts_duckdb()
    source = "duckdb"
    if histograms is None:
        histograms = _year_district_counts_pocketbase()
        source = "pocketbase"

    year_counts, dist_counts = histograms
    for y in HISTORICAL_YEARS:
        year_counts.setdefault(y, 0)
    for d in DISTRICTS:
        dist_counts.setdefault(d, 0)

    year_weights = _target_year_weights(HISTORICAL_YEARS, year_counts)
    district_weights = _inverse_frequency_weights(DISTRICTS, dist_counts)

    sparse_years = [
        y for y in HISTORICAL_YEARS if year_counts.get(y, 0) < TARGET_YEAR_VOLUME
    ]
    sparse_districts = [d for d in DISTRICTS if dist_counts.get(d, 0) < 500]
    year_gaps = {
        str(y): max(0, TARGET_YEAR_VOLUME - year_counts.get(y, 0))
        for y in HISTORICAL_YEARS
        if year_counts.get(y, 0) < TARGET_YEAR_VOLUME
    }

    return {
        "source": source,
        "target_year_volume": TARGET_YEAR_VOLUME,
        "year_choices": HISTORICAL_YEARS,
        "year_weights": year_weights,
        "district_choices": DISTRICTS,
        "district_weights": district_weights,
        "year_counts": year_counts,
        "district_counts": dist_counts,
        "year_gaps_to_target": year_gaps,
        "sparse_years": sparse_years,
        "sparse_districts": sparse_districts,
    }


def gen_crimes_220k_for_year(
    fake,
    year: int,
    *,
    district: int | str | None = None,
) -> dict:
    """Registro crimes_220k con fecha anclada a un año concreto."""
    idx = random.choices(range(len(CHICAGO_CRIME_TYPES)), weights=_CRIME_TYPE_WEIGHTS, k=1)[0]
    primary, iucr, desc, fbi = CHICAGO_CRIME_TYPES[idx]
    dt = _random_datetime_in_year(year)
    lat = round(random.uniform(41.64, 42.02), 6)
    lon = round(random.uniform(-87.94, -87.52), 6)
    if district is None:
        district = str(random.choices(DISTRICTS, weights=_DISTRICT_WEIGHTS, k=1)[0]).zfill(2)
    else:
        district = str(int(district)).zfill(2)
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


def bulk_insert_realistic_crimes(
    total_count: int,
    *,
    workers: int = DEFAULT_WORKERS,
    on_progress: ProgressCallback | None = None,
    gap_fill: bool = True,
) -> dict[str, Any]:
    """Inserta N registros 2001–2026 en chunks de BULK_INSERT_CHUNK; prioriza huecos."""
    del workers
    if total_count < 1:
        raise ValueError("total_count debe ser >= 1")

    gap_meta: dict[str, Any] | None = None
    if gap_fill:
        gap_meta = resolve_gap_fill_weights()
        year_choices = gap_meta["year_choices"]
        year_weights = gap_meta["year_weights"]
        district_choices = gap_meta["district_choices"]
        district_weights = gap_meta["district_weights"]
    else:
        year_choices = YEAR_CHOICES
        year_weights = YEAR_WEIGHTS
        district_choices = DISTRICTS
        district_weights = _DISTRICT_WEIGHTS

    years_plan = random.choices(year_choices, weights=year_weights, k=total_count)
    districts_plan = random.choices(
        district_choices, weights=district_weights, k=total_count
    )
    year_histogram: dict[int, int] = {}
    district_histogram: dict[int, int] = {}
    for y in years_plan:
        year_histogram[y] = year_histogram.get(y, 0) + 1
    for d in districts_plan:
        district_histogram[d] = district_histogram.get(d, 0) + 1

    created = 0
    errors = 0
    samples: list[dict] = []
    error_messages: list[str] = []
    t0 = time.time()
    fake = _fake()

    for offset in range(0, total_count, BULK_INSERT_CHUNK):
        chunk_size = min(BULK_INSERT_CHUNK, total_count - offset)
        chunk_years = years_plan[offset : offset + chunk_size]
        chunk_districts = districts_plan[offset : offset + chunk_size]
        bodies = [
            gen_crimes_220k_for_year(fake, year, district=dist)
            for year, dist in zip(chunk_years, chunk_districts)
        ]

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
            bodies,
            workers=DEFAULT_WORKERS,
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
        "partial": created > 0 and errors > 0,
        "created": created,
        "errors": errors,
        "requested": total_count,
        "elapsed_seconds": elapsed,
        "year_distribution": {str(k): v for k, v in sorted(year_histogram.items())},
        "district_distribution": {str(k): v for k, v in sorted(district_histogram.items())},
        "gap_fill": gap_meta,
        "samples": samples,
        "error_messages": error_messages,
        "message": (
            f"Se insertaron {created} registros realistas en crimes_220k "
            f"(distribuidos 2001–2026, gap-fill={'sí' if gap_fill else 'no'})."
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
