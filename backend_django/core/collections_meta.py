"""Metadatos de colecciones para API y frontend (formularios CRUD)."""

from core.migration.postgres_config import DIMENSION_MIGRATIONS
from core.services.minio_store import MINIO_STAR_COLLECTIONS, POCKETBASE_ONLY_COLLECTIONS

FieldDef = dict  # {name, label, type: text|number|bool|date, required?}

def _fields_from_columns(columns: dict[str, str], labels: dict[str, str] | None = None) -> list[FieldDef]:
    labels = labels or {}
    result = [{"name": "legacy_id", "label": "ID legado (Postgres)", "type": "number"}]
    for col in columns:
        result.append(
            {
                "name": col,
                "label": labels.get(col, col.replace("_", " ").title()),
                "type": _guess_type(col),
            }
        )
    return result


def _guess_type(name: str) -> str:
    if name.startswith("es_") or name.startswith("hubo_") or name in (
        "fianza_requerida",
        "requiere_arma",
        "es_reincidente",
        "vigilancia_camaras",
        "victima_menor_edad",
        "intervencion_social",
        "reincidencia",
    ):
        return "bool"
    if "fecha" in name:
        return "date"
    if name in (
        "poblacion_estimada",
        "superficie_km2",
        "numero_oficiales",
        "monto_fianza",
        "updated_year",
        "updated_month",
        "updated_day",
        "version_registro",
        "month",
        "day",
        "hour",
        "quarter",
    ) or name.startswith("fk_"):
        return "number"
    return "text"


DIM_LABELS: dict[str, str] = {
    "dim_actualizacion": "Actualización",
    "dim_area_administrativa": "Área administrativa",
    "dim_arresto": "Arresto",
    "dim_caso": "Caso",
    "dim_distrito_policial": "Distrito policial",
    "dim_tiempo": "Tiempo",
    "dim_tipo_crimen": "Tipo de crimen",
    "dim_ubicacion_geografica": "Ubicación geográfica",
    "dim_ubicacion_lugar": "Ubicación / lugar",
    "dim_violencia_domestica": "Violencia doméstica",
    "fact_crimes": "Hechos delictivos (fact)",
    "crimes_220k": "Crímenes raw (staging)",
}

COLLECTIONS: dict[str, dict] = {}

for mig in DIMENSION_MIGRATIONS:
    COLLECTIONS[mig.pb_collection] = {
        "slug": mig.pb_collection,
        "label": DIM_LABELS.get(mig.pb_collection, mig.pb_collection),
        "icon": "table",
        "storage": "minio",
        "fields": _fields_from_columns(mig.columns),
        "group": "dimension",
    }

COLLECTIONS["fact_crimes"] = {
    "slug": "fact_crimes",
    "label": DIM_LABELS["fact_crimes"],
    "icon": "shield",
    "storage": "minio",
    "group": "fact",
    "fields": [
        {"name": "id", "label": "ID", "type": "number"},
        {"name": "raw_row_id", "label": "Fila raw (PB)", "type": "text"},
        {"name": "fk_caso", "label": "FK Caso", "type": "number"},
        {"name": "fk_tipo_crimen", "label": "FK Tipo crimen", "type": "number"},
        {"name": "fk_distrito", "label": "FK Distrito", "type": "number"},
        {"name": "fk_area", "label": "FK Área", "type": "number"},
        {"name": "fk_tiempo", "label": "FK Tiempo", "type": "number"},
        {"name": "fk_ubicacion_lugar", "label": "FK Lugar", "type": "number"},
        {"name": "fk_ubicacion_geo", "label": "FK Geo", "type": "number"},
        {"name": "fk_arresto", "label": "FK Arresto", "type": "number"},
        {"name": "fk_domestico", "label": "FK Doméstico", "type": "number"},
        {"name": "fk_actualizacion", "label": "FK Actualización", "type": "number"},
    ],
    "relations": [
        {"name": "fk_caso", "label": "Caso", "collection": "dim_caso"},
        {"name": "fk_tipo_crimen", "label": "Tipo crimen", "collection": "dim_tipo_crimen"},
        {"name": "fk_ubicacion_lugar", "label": "Lugar", "collection": "dim_ubicacion_lugar"},
        {"name": "fk_ubicacion_geo", "label": "Geo", "collection": "dim_ubicacion_geografica"},
        {"name": "fk_distrito", "label": "Distrito", "collection": "dim_distrito_policial"},
        {"name": "fk_area", "label": "Área", "collection": "dim_area_administrativa"},
        {"name": "fk_tiempo", "label": "Tiempo", "collection": "dim_tiempo"},
        {"name": "fk_actualizacion", "label": "Actualización", "collection": "dim_actualizacion"},
        {"name": "fk_arresto", "label": "Arresto", "collection": "dim_arresto"},
        {"name": "fk_domestico", "label": "Doméstico", "collection": "dim_violencia_domestica"},
    ],
}

COLLECTIONS["crimes_220k"] = {
    "slug": "crimes_220k",
    "label": DIM_LABELS["crimes_220k"],
    "icon": "database",
    "storage": "pocketbase",
    "group": "raw",
    "read_only_hint": True,
    "fields": _fields_from_columns(
        {
            "id": "id",
            "case_number": "case_number",
            "date": "date",
            "block": "block",
            "iucr": "iucr",
            "primary_type": "primary_type",
            "description": "description",
            "location_description": "location_description",
            "arrest": "arrest",
            "domestic": "domestic",
            "beat": "beat",
            "district": "district",
            "ward": "ward",
            "community_area": "community_area",
            "fbi_code": "fbi_code",
            "latitude": "latitude",
            "longitude": "longitude",
            "location": "location",
        }
    ),
}

ALLOWED_COLLECTIONS = frozenset(COLLECTIONS.keys())


def collection_storage(slug: str) -> str:
    if slug in POCKETBASE_ONLY_COLLECTIONS:
        return "pocketbase"
    if slug in MINIO_STAR_COLLECTIONS:
        return "minio"
    return COLLECTIONS.get(slug, {}).get("storage", "minio")
