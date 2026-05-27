"""
Mapeo PostgreSQL → PocketBase (uso único: comando migrate_from_postgres).

Tras la migración, CrimeTrack no depende de Postgres; PocketBase es la fuente de verdad.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DimensionMigration:
    pg_table: str
    pb_collection: str
    pg_pk: str
    # pg_column -> pb_field (mismos nombres salvo legacy_id)
    columns: dict[str, str] = field(default_factory=dict)


DIMENSION_MIGRATIONS: list[DimensionMigration] = [
    DimensionMigration(
        "dim_actualizacion",
        "dim_actualizacion",
        "id_actualizacion",
        {
            "updated_on": "updated_on",
            "updated_year": "updated_year",
            "updated_month": "updated_month",
            "updated_day": "updated_day",
            "usuario_actualizador": "usuario_actualizador",
            "sistema_origen": "sistema_origen",
            "motivo_actualizacion": "motivo_actualizacion",
            "version_registro": "version_registro",
        },
    ),
    DimensionMigration(
        "dim_area_administrativa",
        "dim_area_administrativa",
        "id_area",
        {
            "ward": "ward",
            "community_area": "community_area",
            "nombre_comunidad": "nombre_comunidad",
            "poblacion_estimada": "poblacion_estimada",
            "alcalde_representante": "alcalde_representante",
            "nivel_socioeconomico": "nivel_socioeconomico",
            "superficie_km2": "superficie_km2",
        },
    ),
    DimensionMigration(
        "dim_arresto",
        "dim_arresto",
        "id_arresto",
        {
            "arrest": "arrest",
            "descripcion_arresto": "descripcion_arresto",
            "fecha_arresto": "fecha_arresto",
            "lugar_detencion": "lugar_detencion",
            "oficial_a_cargo": "oficial_a_cargo",
            "tipo_cargo": "tipo_cargo",
            "fianza_requerida": "fianza_requerida",
            "monto_fianza": "monto_fianza",
        },
    ),
    DimensionMigration(
        "dim_caso",
        "dim_caso",
        "id_caso",
        {
            "case_number": "case_number",
            "estado_caso": "estado_caso",
            "fecha_reporte": "fecha_reporte",
            "investigador_asignado": "investigador_asignado",
            "prioridad_caso": "prioridad_caso",
            "observaciones": "observaciones",
        },
    ),
    DimensionMigration(
        "dim_distrito_policial",
        "dim_distrito_policial",
        "id_distrito",
        {
            "beat": "beat",
            "district": "district",
            "nombre_distrito": "nombre_distrito",
            "jefe_distrito": "jefe_distrito",
            "numero_oficiales": "numero_oficiales",
            "telefono_emergencias": "telefono_emergencias",
            "direccion_sede": "direccion_sede",
            "horario_atencion": "horario_atencion",
        },
    ),
    DimensionMigration(
        "dim_tiempo",
        "dim_tiempo",
        "id_tiempo",
        {
            "date": "date",
            "year": "year",
            "month": "month",
            "day": "day",
            "hour": "hour",
            "day_of_week": "day_of_week",
            "quarter": "quarter",
            "es_fin_de_semana": "es_fin_de_semana",
            "es_feriado": "es_feriado",
            "temporada": "temporada",
            "turno": "turno",
        },
    ),
    DimensionMigration(
        "dim_tipo_crimen",
        "dim_tipo_crimen",
        "id_tipo_crimen",
        {
            "iucr": "iucr",
            "primary_type": "primary_type",
            "description": "description",
            "fbi_code": "fbi_code",
            "nivel_gravedad": "nivel_gravedad",
            "categoria_penal": "categoria_penal",
            "requiere_arma": "requiere_arma",
            "es_reincidente": "es_reincidente",
        },
    ),
    DimensionMigration(
        "dim_ubicacion_geografica",
        "dim_ubicacion_geografica",
        "id_ubicacion_geo",
        {
            "x_coordinate": "x_coordinate",
            "y_coordinate": "y_coordinate",
            "latitude": "latitude",
            "longitude": "longitude",
            "location": "location",
            "ciudad": "ciudad",
            "estado": "estado",
            "pais": "pais",
            "codigo_postal": "codigo_postal",
            "nombre_sector": "nombre_sector",
        },
    ),
    DimensionMigration(
        "dim_ubicacion_lugar",
        "dim_ubicacion_lugar",
        "id_ubicacion_lugar",
        {
            "location_description": "location_description",
            "block": "block",
            "tipo_zona": "tipo_zona",
            "nivel_riesgo": "nivel_riesgo",
            "iluminacion": "iluminacion",
            "vigilancia_camaras": "vigilancia_camaras",
        },
    ),
    DimensionMigration(
        "dim_violencia_domestica",
        "dim_violencia_domestica",
        "id_domestico",
        {
            "domestic": "domestic",
            "descripcion_domestico": "descripcion_domestico",
            "tipo_relacion_victima": "tipo_relacion_victima",
            "hubo_orden_restriccion": "hubo_orden_restriccion",
            "victima_menor_edad": "victima_menor_edad",
            "intervencion_social": "intervencion_social",
            "reincidencia": "reincidencia",
        },
    ),
]

# fact_crimes: columna FK Postgres → (campo relación PB, colección dim para mapa)
FACT_RELATIONS: dict[str, tuple[str, str]] = {
    "id_caso": ("caso", "dim_caso"),
    "id_tipo_crimen": ("tipo_crimen", "dim_tipo_crimen"),
    "id_ubicacion_lugar": ("ubicacion_lugar", "dim_ubicacion_lugar"),
    "id_ubicacion_geo": ("ubicacion_geo", "dim_ubicacion_geografica"),
    "id_distrito": ("distrito", "dim_distrito_policial"),
    "id_area": ("area", "dim_area_administrativa"),
    "id_tiempo": ("tiempo", "dim_tiempo"),
    "id_actualizacion": ("actualizacion", "dim_actualizacion"),
    "id_arresto": ("arresto", "dim_arresto"),
    "id_domestico": ("domestico", "dim_violencia_domestica"),
}

CRIMES_220K_COLUMNS: dict[str, str] = {
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
    "x_coordinate": "x_coordinate",
    "y_coordinate": "y_coordinate",
    "year": "year",
    "updated_on": "updated_on",
    "latitude": "latitude",
    "longitude": "longitude",
    "location": "location",
    "fk_caso": "fk_caso",
    "fk_tipo_crimen": "fk_tipo_crimen",
    "fk_ubicacion_lugar": "fk_ubicacion_lugar",
    "fk_ubicacion_geo": "fk_ubicacion_geo",
    "fk_distrito": "fk_distrito",
    "fk_area": "fk_area",
    "fk_tiempo": "fk_tiempo",
    "fk_actualizacion": "fk_actualizacion",
    "fk_arresto": "fk_arresto",
    "fk_domestico": "fk_domestico",
}
