"""
Esquema PocketBase alineado al modelo estrella PostgreSQL (pgAdmin ERD).

dims  -> dim_* colecciones
fact  -> fact_crimes (relaciones a cada dim)
raw   -> crimes_220k (staging plano para ETL desde Postgres)
"""

from core.pocketbase.fields import bool_field, date_field, number_field, text_field

def legacy_id_field() -> dict:
    """ID serial de Postgres conservado durante la migración ETL."""
    return number_field("legacy_id", no_decimal=True)

DIMENSION_SCHEMAS: list[dict] = [
    {
        "name": "dim_actualizacion",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("updated_on"),
            number_field("updated_year", no_decimal=True),
            number_field("updated_month", no_decimal=True),
            number_field("updated_day", no_decimal=True),
            text_field("usuario_actualizador"),
            text_field("sistema_origen"),
            text_field("motivo_actualizacion"),
            number_field("version_registro", no_decimal=True),
        ],
    },
    {
        "name": "dim_area_administrativa",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("ward"),
            text_field("community_area"),
            text_field("nombre_comunidad"),
            number_field("poblacion_estimada", no_decimal=True),
            text_field("alcalde_representante"),
            text_field("nivel_socioeconomico"),
            number_field("superficie_km2"),
        ],
    },
    {
        "name": "dim_arresto",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("arrest"),
            text_field("descripcion_arresto"),
            date_field("fecha_arresto"),
            text_field("lugar_detencion"),
            text_field("oficial_a_cargo"),
            text_field("tipo_cargo"),
            bool_field("fianza_requerida"),
            number_field("monto_fianza"),
        ],
    },
    {
        "name": "dim_caso",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("case_number"),
            text_field("estado_caso"),
            date_field("fecha_reporte"),
            text_field("investigador_asignado"),
            text_field("prioridad_caso"),
            text_field("observaciones"),
        ],
    },
    {
        "name": "dim_distrito_policial",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("beat"),
            text_field("district"),
            text_field("nombre_distrito"),
            text_field("jefe_distrito"),
            number_field("numero_oficiales", no_decimal=True),
            text_field("telefono_emergencias"),
            text_field("direccion_sede"),
            text_field("horario_atencion"),
        ],
    },
    {
        "name": "dim_tiempo",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("date"),
            text_field("year"),
            number_field("month", no_decimal=True),
            number_field("day", no_decimal=True),
            number_field("hour", no_decimal=True),
            text_field("day_of_week"),
            number_field("quarter", no_decimal=True),
            bool_field("es_fin_de_semana"),
            bool_field("es_feriado"),
            text_field("temporada"),
            text_field("turno"),
        ],
    },
    {
        "name": "dim_tipo_crimen",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("iucr"),
            text_field("primary_type"),
            text_field("description"),
            text_field("fbi_code"),
            text_field("nivel_gravedad"),
            text_field("categoria_penal"),
            bool_field("requiere_arma"),
            bool_field("es_reincidente"),
        ],
    },
    {
        "name": "dim_ubicacion_geografica",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("x_coordinate"),
            text_field("y_coordinate"),
            text_field("latitude"),
            text_field("longitude"),
            text_field("location"),
            text_field("ciudad"),
            text_field("estado"),
            text_field("pais"),
            text_field("codigo_postal"),
            text_field("nombre_sector"),
        ],
    },
    {
        "name": "dim_ubicacion_lugar",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("location_description"),
            text_field("block"),
            text_field("tipo_zona"),
            text_field("nivel_riesgo"),
            text_field("iluminacion"),
            bool_field("vigilancia_camaras"),
        ],
    },
    {
        "name": "dim_violencia_domestica",
        "type": "base",
        "fields": [
            legacy_id_field(),
            text_field("domestic"),
            text_field("descripcion_domestico"),
            text_field("tipo_relacion_victima"),
            bool_field("hubo_orden_restriccion"),
            bool_field("victima_menor_edad"),
            bool_field("intervencion_social"),
            bool_field("reincidencia"),
        ],
    },
]

# Tabla plana crimes_220k de Postgres (staging para migración)
CRIMES_220K_SCHEMA: dict = {
    "name": "crimes_220k",
    "type": "base",
    "fields": [
        text_field("id"),
        text_field("case_number"),
        text_field("date"),
        text_field("block"),
        text_field("iucr"),
        text_field("primary_type"),
        text_field("description"),
        text_field("location_description"),
        text_field("arrest"),
        text_field("domestic"),
        text_field("beat"),
        text_field("district"),
        text_field("ward"),
        text_field("community_area"),
        text_field("fbi_code"),
        text_field("x_coordinate"),
        text_field("y_coordinate"),
        text_field("year"),
        text_field("updated_on"),
        text_field("latitude"),
        text_field("longitude"),
        text_field("location"),
        number_field("fk_caso", no_decimal=True),
        number_field("fk_tipo_crimen", no_decimal=True),
        number_field("fk_ubicacion_lugar", no_decimal=True),
        number_field("fk_ubicacion_geo", no_decimal=True),
        number_field("fk_distrito", no_decimal=True),
        number_field("fk_area", no_decimal=True),
        number_field("fk_tiempo", no_decimal=True),
        number_field("fk_actualizacion", no_decimal=True),
        number_field("fk_arresto", no_decimal=True),
        number_field("fk_domestico", no_decimal=True),
    ],
}

FACT_RELATION_NAMES = {
    "caso": "dim_caso",
    "tipo_crimen": "dim_tipo_crimen",
    "ubicacion_lugar": "dim_ubicacion_lugar",
    "ubicacion_geo": "dim_ubicacion_geografica",
    "distrito": "dim_distrito_policial",
    "area": "dim_area_administrativa",
    "tiempo": "dim_tiempo",
    "actualizacion": "dim_actualizacion",
    "arresto": "dim_arresto",
    "domestico": "dim_violencia_domestica",
}


def build_fact_crimes_schema(collection_ids: dict[str, str]) -> dict:
    fields = [legacy_id_field()]
    for rel_name, dim_name in FACT_RELATION_NAMES.items():
        from core.pocketbase.fields import relation_field

        fields.append(relation_field(rel_name, collection_ids[dim_name]))
    return {
        "name": "fact_crimes",
        "type": "base",
        "fields": fields,
    }
