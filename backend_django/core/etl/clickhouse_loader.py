"""
Loader analítico MinIO -> ClickHouse (capa TÁCTICA / ESTRATÉGICA).

Responsabilidad: leer los Parquet de MinIO (modelo estrella + operativo) y
materializarlos en las tablas analíticas de ClickHouse (crimetrack_analytics).

NO toca la capa operativa: solo LEE de MinIO y ESCRIBE en ClickHouse. Es la
lógica que el comando `manage.py clickhouse_sync` y el DAG de Airflow invocan.

Estrategia de carga: full refresh idempotente (TRUNCATE + INSERT) por tabla,
adecuado para una base analítica de solo lectura.
"""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from core.services.analytics_service import AnalyticsService
from core.services.clickhouse_client import ClickHouseService
from core.services.minio_store import MinioParquetStore
from packages.shared.minio_transactional import TransactionalMinioStore

ProgressFn = Callable[[str], None]


# --------------------------------------------------------------------------
# DDL embebido (espejo de infra/clickhouse/init/*.sql) para que el backend
# pueda crear el esquema aunque el contenedor ya se hubiera inicializado.
# --------------------------------------------------------------------------
DDL_DATABASE = "CREATE DATABASE IF NOT EXISTS crimetrack_analytics"

DDL_TABLES: dict[str, str] = {
    "dim_fecha": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_fecha (
            id UInt64, date String, year UInt16, month UInt8, day UInt8,
            hour UInt8, day_of_week String, quarter UInt8,
            es_fin_de_semana UInt8, temporada String, turno String
        ) ENGINE = MergeTree ORDER BY (id)
    """,
    "dim_tipo_crimen": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_tipo_crimen (
            id UInt64, iucr String, primary_type String, description String,
            fbi_code String, nivel_gravedad String, categoria_penal String
        ) ENGINE = MergeTree ORDER BY (id)
    """,
    "dim_ubicacion": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_ubicacion (
            id UInt64, district String, beat String, nombre_distrito String,
            ward String, community_area String, location_description String,
            block String, latitude String, longitude String,
            tipo_zona String, nivel_riesgo String
        ) ENGINE = MergeTree ORDER BY (id)
    """,
    "dim_usuario": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_usuario (
            id UInt64, fk_rol String, nombre_rol String, numero_placa String,
            nombres String, apellidos String, email String,
            estado_cuenta String, fecha_creacion String
        ) ENGINE = MergeTree ORDER BY (id)
    """,
    "dim_estado": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_estado (
            id UInt32, ambito String, codigo String, descripcion String
        ) ENGINE = MergeTree ORDER BY (ambito, codigo)
    """,
    "dim_patrulla": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_patrulla (
            id UInt64, codigo String, sector String, turno String,
            estado String, fk_comisario String, comisario_nombre String,
            activo UInt8, fecha_creacion String
        ) ENGINE = MergeTree ORDER BY (id)
    """,
    "fact_crimes": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_crimes (
            id UInt64, raw_row_id String, fk_caso UInt64, fk_tipo_crimen UInt64,
            fk_distrito UInt64, fk_tiempo UInt64, case_number String, iucr String,
            primary_type String, fbi_code String, district String, beat String,
            ward String, community_area String, location_description String,
            block String, latitude String, longitude String, date String,
            year UInt16, month UInt8, arrest UInt8, domestic UInt8,
            estado_caso String, prioridad_caso String
        ) ENGINE = MergeTree PARTITION BY year ORDER BY (year, district, primary_type, id)
    """,
    "fact_incidentes": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_incidentes (
            id UInt64, codigo String, tipo String, prioridad String, estado String,
            ubicacion String, reportante String, fk_patrulla String,
            patrulla_codigo String, fk_operador String, operador_nombre String,
            fk_comisario String, comisario_nombre String, fk_expediente String,
            expediente_case_number String, fecha_reporte String, fecha_despacho String,
            fecha_atendido String, fecha_cierre String
        ) ENGINE = MergeTree ORDER BY (estado, id)
    """,
    "fact_expedientes": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_expedientes (
            id UInt64, case_number String, fk_caso String, titulo String,
            tipo_delito String, prioridad String, estado String, distrito String,
            sector String, zona String, iucr String, fbi_code String,
            arresto UInt8, violencia_domestica UInt8, fecha_hecho String,
            creado_en String, creador_nombre String
        ) ENGINE = MergeTree ORDER BY (estado, id)
    """,
    "fact_evidencias": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_evidencias (
            id UInt64, fk_caso String, tipo_evidencia String, nombre_archivo String,
            peso_mb Float64, algoritmo_hash String, estado_custodia String,
            fk_usuario_carga String, fecha_subida String
        ) ENGINE = MergeTree ORDER BY (estado_custodia, id)
    """,
    "fact_auditoria": """
        CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_auditoria (
            id UInt64, fk_usuario String, accion String, tabla_afectada String,
            direccion_ip String, fecha_hora String
        ) ENGINE = MergeTree ORDER BY (tabla_afectada, id)
    """,
}

# Especificación de columnas por tabla: (col_clickhouse, col_origen, tipo)
ColSpec = tuple[str, str, str]


# --------------------------------------------------------------------------
# Utilidades de coerción de tipos
# --------------------------------------------------------------------------
def _str(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).replace({"None": "", "nan": ""})


def _int(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0).astype("int64")


def _float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0.0).astype("float64")


_TRUE = {"true", "1", "yes", "si", "sí", "y", "t", "verdadero"}


def _bool(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.lower().isin(_TRUE).astype("uint8")


def _prepare(df: pd.DataFrame, spec: list[ColSpec]) -> pd.DataFrame:
    """Construye un DataFrame con las columnas/tipos exactos de ClickHouse."""
    out = pd.DataFrame()
    coercers = {"str": _str, "int": _int, "float": _float, "bool": _bool}
    for ch_col, src_col, kind in spec:
        src = df[src_col] if src_col in df.columns else pd.Series([None] * len(df))
        out[ch_col] = coercers[kind](src)
    return out


# --------------------------------------------------------------------------
# Esquema
# --------------------------------------------------------------------------
def ensure_schema(ch: ClickHouseService) -> None:
    ch.command(DDL_DATABASE)
    for ddl in DDL_TABLES.values():
        ch.command(ddl)


def _truncate_and_insert(ch: ClickHouseService, table: str, df: pd.DataFrame) -> int:
    ch.command(f"TRUNCATE TABLE IF EXISTS crimetrack_analytics.{table}")
    if df is None or df.empty:
        return 0
    return ch.insert_df(table, df)


# --------------------------------------------------------------------------
# Carga de dimensiones (modelo estrella + operativo)
# --------------------------------------------------------------------------
def load_dim_fecha(ch: ClickHouseService, star: MinioParquetStore) -> int:
    df = star.read_df("dim_tiempo", use_cache=False)
    spec: list[ColSpec] = [
        ("id", "id", "int"), ("date", "date", "str"), ("year", "year", "int"),
        ("month", "month", "int"), ("day", "day", "int"), ("hour", "hour", "int"),
        ("day_of_week", "day_of_week", "str"), ("quarter", "quarter", "int"),
        ("es_fin_de_semana", "es_fin_de_semana", "bool"),
        ("temporada", "temporada", "str"), ("turno", "turno", "str"),
    ]
    return _truncate_and_insert(ch, "dim_fecha", _prepare(df, spec))


def load_dim_tipo_crimen(ch: ClickHouseService, star: MinioParquetStore) -> int:
    df = star.read_df("dim_tipo_crimen", use_cache=False)
    spec: list[ColSpec] = [
        ("id", "id", "int"), ("iucr", "iucr", "str"), ("primary_type", "primary_type", "str"),
        ("description", "description", "str"), ("fbi_code", "fbi_code", "str"),
        ("nivel_gravedad", "nivel_gravedad", "str"), ("categoria_penal", "categoria_penal", "str"),
    ]
    return _truncate_and_insert(ch, "dim_tipo_crimen", _prepare(df, spec))


def load_dim_ubicacion(ch: ClickHouseService, star: MinioParquetStore) -> int:
    # SUPUESTO: clave = dim_distrito_policial.id (FK que usa fact_crimes.fk_distrito).
    # Los campos de área/lugar/geo quedan vacíos (normalizados en otras dims).
    df = star.read_df("dim_distrito_policial", use_cache=False)
    spec: list[ColSpec] = [
        ("id", "id", "int"), ("district", "district", "str"), ("beat", "beat", "str"),
        ("nombre_distrito", "nombre_distrito", "str"), ("ward", "__none__", "str"),
        ("community_area", "__none__", "str"), ("location_description", "__none__", "str"),
        ("block", "__none__", "str"), ("latitude", "__none__", "str"),
        ("longitude", "__none__", "str"), ("tipo_zona", "__none__", "str"),
        ("nivel_riesgo", "__none__", "str"),
    ]
    return _truncate_and_insert(ch, "dim_ubicacion", _prepare(df, spec))


def load_dim_usuario(ch: ClickHouseService, tx: TransactionalMinioStore) -> int:
    df = tx.read_table("app_usuarios")
    roles = tx.read_table("app_roles")
    if not df.empty and not roles.empty:
        rmap = dict(zip(roles["id_rol"].astype(str), roles["nombre_rol"].astype(str)))
        df = df.copy()
        df["nombre_rol"] = df["fk_rol"].astype(str).map(rmap).fillna("")
    else:
        df = df.copy()
        df["nombre_rol"] = ""
    spec: list[ColSpec] = [
        ("id", "id_usuario", "int"), ("fk_rol", "fk_rol", "str"),
        ("nombre_rol", "nombre_rol", "str"), ("numero_placa", "numero_placa", "str"),
        ("nombres", "nombres", "str"), ("apellidos", "apellidos", "str"),
        ("email", "email", "str"), ("estado_cuenta", "estado_cuenta", "str"),
        ("fecha_creacion", "fecha_creacion", "str"),
    ]
    return _truncate_and_insert(ch, "dim_usuario", _prepare(df, spec))


def load_dim_patrulla(ch: ClickHouseService, tx: TransactionalMinioStore) -> int:
    df = tx.read_table("app_patrullas")
    spec: list[ColSpec] = [
        ("id", "id_patrulla", "int"), ("codigo", "codigo", "str"), ("sector", "sector", "str"),
        ("turno", "turno", "str"), ("estado", "estado", "str"),
        ("fk_comisario", "fk_comisario", "str"), ("comisario_nombre", "comisario_nombre", "str"),
        ("activo", "activo", "bool"), ("fecha_creacion", "fecha_creacion", "str"),
    ]
    return _truncate_and_insert(ch, "dim_patrulla", _prepare(df, spec))


def load_dim_estado(ch: ClickHouseService, tx: TransactionalMinioStore) -> int:
    # Catálogo derivado: valores DISTINCT de estado por ámbito operativo.
    sources = [
        ("expediente", "app_expedientes", "estado"),
        ("incidente", "app_incidentes", "estado"),
        ("caso", "app_casos_operativos", "estado_caso"),
        ("asignacion", "app_asignaciones", "estado_asignacion"),
        ("evidencia", "app_evidencias", "estado_custodia"),
    ]
    rows: list[dict[str, Any]] = []
    next_id = 1
    for ambito, tabla, col in sources:
        try:
            df = tx.read_table(tabla)
        except Exception:
            continue
        if df.empty or col not in df.columns:
            continue
        for val in sorted({str(v).strip() for v in df[col].dropna() if str(v).strip()}):
            rows.append({"id": next_id, "ambito": ambito, "codigo": val, "descripcion": ""})
            next_id += 1
    out = pd.DataFrame(rows, columns=["id", "ambito", "codigo", "descripcion"])
    if not out.empty:
        out["id"] = out["id"].astype("int64")
        out["ambito"] = out["ambito"].astype(str)
        out["codigo"] = out["codigo"].astype(str)
        out["descripcion"] = out["descripcion"].astype(str)
    return _truncate_and_insert(ch, "dim_estado", out)


# --------------------------------------------------------------------------
# Carga de hechos operativos (datasets/transactional/)
# --------------------------------------------------------------------------
def load_fact_incidentes(ch: ClickHouseService, tx: TransactionalMinioStore) -> int:
    df = tx.read_table("app_incidentes")
    spec: list[ColSpec] = [
        ("id", "id_incidente", "int"), ("codigo", "codigo", "str"), ("tipo", "tipo", "str"),
        ("prioridad", "prioridad", "str"), ("estado", "estado", "str"),
        ("ubicacion", "ubicacion", "str"), ("reportante", "reportante", "str"),
        ("fk_patrulla", "fk_patrulla", "str"), ("patrulla_codigo", "patrulla_codigo", "str"),
        ("fk_operador", "fk_operador", "str"), ("operador_nombre", "operador_nombre", "str"),
        ("fk_comisario", "fk_comisario", "str"), ("comisario_nombre", "comisario_nombre", "str"),
        ("fk_expediente", "fk_expediente", "str"),
        ("expediente_case_number", "expediente_case_number", "str"),
        ("fecha_reporte", "fecha_reporte", "str"), ("fecha_despacho", "fecha_despacho", "str"),
        ("fecha_atendido", "fecha_atendido", "str"), ("fecha_cierre", "fecha_cierre", "str"),
    ]
    return _truncate_and_insert(ch, "fact_incidentes", _prepare(df, spec))


def load_fact_expedientes(ch: ClickHouseService, tx: TransactionalMinioStore) -> int:
    df = tx.read_table("app_expedientes")
    spec: list[ColSpec] = [
        ("id", "id_expediente", "int"), ("case_number", "case_number", "str"),
        ("fk_caso", "fk_caso", "str"), ("titulo", "titulo", "str"),
        ("tipo_delito", "tipo_delito", "str"), ("prioridad", "prioridad", "str"),
        ("estado", "estado", "str"), ("distrito", "distrito", "str"),
        ("sector", "sector", "str"), ("zona", "zona", "str"), ("iucr", "iucr", "str"),
        ("fbi_code", "fbi_code", "str"), ("arresto", "arresto", "bool"),
        ("violencia_domestica", "violencia_domestica", "bool"),
        ("fecha_hecho", "fecha_hecho", "str"), ("creado_en", "creado_en", "str"),
        ("creador_nombre", "creador_nombre", "str"),
    ]
    return _truncate_and_insert(ch, "fact_expedientes", _prepare(df, spec))


def load_fact_evidencias(ch: ClickHouseService, tx: TransactionalMinioStore) -> int:
    df = tx.read_table("app_evidencias")
    spec: list[ColSpec] = [
        ("id", "id_evidencia", "int"), ("fk_caso", "fk_caso", "str"),
        ("tipo_evidencia", "tipo_evidencia", "str"), ("nombre_archivo", "nombre_archivo", "str"),
        ("peso_mb", "peso_mb", "float"), ("algoritmo_hash", "algoritmo_hash", "str"),
        ("estado_custodia", "estado_custodia", "str"),
        ("fk_usuario_carga", "fk_usuario_carga", "str"), ("fecha_subida", "fecha_subida", "str"),
    ]
    return _truncate_and_insert(ch, "fact_evidencias", _prepare(df, spec))


def load_fact_auditoria(ch: ClickHouseService, tx: TransactionalMinioStore) -> int:
    df = tx.read_table("app_audit_logs")
    spec: list[ColSpec] = [
        ("id", "id_log", "int"), ("fk_usuario", "fk_usuario", "str"),
        ("accion", "accion", "str"), ("tabla_afectada", "tabla_afectada", "str"),
        ("direccion_ip", "direccion_ip", "str"), ("fecha_hora", "fecha_hora", "str"),
    ]
    return _truncate_and_insert(ch, "fact_auditoria", _prepare(df, spec))


# --------------------------------------------------------------------------
# Carga de fact_crimes (desnormalizado desde el modelo estrella vía DuckDB)
# --------------------------------------------------------------------------
def _fact_crimes_sql(an: AnalyticsService) -> str:
    fact = an._fact_parquet_source()
    dc = an._dim_parquet("dim_caso")
    t = an._dim_parquet("dim_tipo_crimen")
    d = an._dim_parquet("dim_distrito_policial")
    a = an._dim_parquet("dim_area_administrativa")
    tm = an._dim_parquet("dim_tiempo")
    l = an._dim_parquet("dim_ubicacion_lugar")
    g = an._dim_parquet("dim_ubicacion_geografica")
    ar = an._dim_parquet("dim_arresto")
    vd = an._dim_parquet("dim_violencia_domestica")
    return f"""
        SELECT
            CAST(f.id AS BIGINT) AS id,
            CAST(f.raw_row_id AS VARCHAR) AS raw_row_id,
            CAST(f.fk_caso AS BIGINT) AS fk_caso,
            CAST(f.fk_tipo_crimen AS BIGINT) AS fk_tipo_crimen,
            CAST(f.fk_distrito AS BIGINT) AS fk_distrito,
            CAST(f.fk_tiempo AS BIGINT) AS fk_tiempo,
            CAST(dc.case_number AS VARCHAR) AS case_number,
            CAST(t.iucr AS VARCHAR) AS iucr,
            CAST(t.primary_type AS VARCHAR) AS primary_type,
            CAST(t.fbi_code AS VARCHAR) AS fbi_code,
            CAST(d.district AS VARCHAR) AS district,
            CAST(d.beat AS VARCHAR) AS beat,
            CAST(a.ward AS VARCHAR) AS ward,
            CAST(a.community_area AS VARCHAR) AS community_area,
            CAST(l.location_description AS VARCHAR) AS location_description,
            CAST(l.block AS VARCHAR) AS block,
            CAST(g.latitude AS VARCHAR) AS latitude,
            CAST(g.longitude AS VARCHAR) AS longitude,
            CAST(tm.date AS VARCHAR) AS date,
            CASE WHEN TRY_CAST(tm.year AS INTEGER) BETWEEN 1900 AND 2200
                 THEN TRY_CAST(tm.year AS INTEGER) ELSE 0 END AS year,
            COALESCE(TRY_CAST(tm.month AS INTEGER), 0) AS month,
            CASE WHEN lower(CAST(ar.arrest AS VARCHAR)) IN ('true','1','yes','t') THEN 1 ELSE 0 END AS arrest,
            CASE WHEN lower(CAST(vd.domestic AS VARCHAR)) IN ('true','1','yes','t') THEN 1 ELSE 0 END AS domestic,
            CAST(dc.estado_caso AS VARCHAR) AS estado_caso,
            CAST(dc.prioridad_caso AS VARCHAR) AS prioridad_caso
        FROM read_parquet('{fact}') AS f
        LEFT JOIN read_parquet('{dc}') AS dc ON CAST(f.fk_caso AS BIGINT) = CAST(dc.id AS BIGINT)
        LEFT JOIN read_parquet('{t}') AS t ON CAST(f.fk_tipo_crimen AS BIGINT) = CAST(t.id AS BIGINT)
        LEFT JOIN read_parquet('{d}') AS d ON CAST(f.fk_distrito AS BIGINT) = CAST(d.id AS BIGINT)
        LEFT JOIN read_parquet('{a}') AS a ON CAST(f.fk_area AS BIGINT) = CAST(a.id AS BIGINT)
        LEFT JOIN read_parquet('{tm}') AS tm ON CAST(f.fk_tiempo AS BIGINT) = CAST(tm.id AS BIGINT)
        LEFT JOIN read_parquet('{l}') AS l ON CAST(f.fk_ubicacion_lugar AS BIGINT) = CAST(l.id AS BIGINT)
        LEFT JOIN read_parquet('{g}') AS g ON CAST(f.fk_ubicacion_geo AS BIGINT) = CAST(g.id AS BIGINT)
        LEFT JOIN read_parquet('{ar}') AS ar ON CAST(f.fk_arresto AS BIGINT) = CAST(ar.id AS BIGINT)
        LEFT JOIN read_parquet('{vd}') AS vd ON CAST(f.fk_domestico AS BIGINT) = CAST(vd.id AS BIGINT)
    """


_FACT_STR_COLS = [
    "raw_row_id", "case_number", "iucr", "primary_type", "fbi_code", "district",
    "beat", "ward", "community_area", "location_description", "block", "latitude",
    "longitude", "date", "estado_caso", "prioridad_caso",
]
_FACT_INT_COLS = ["id", "fk_caso", "fk_tipo_crimen", "fk_distrito", "fk_tiempo"]
_FACT_SMALL_COLS = ["year", "month", "arrest", "domestic"]


def load_fact_crimes(
    ch: ClickHouseService,
    star: MinioParquetStore,
    *,
    chunk_vectors: int = 256,
    on_progress: ProgressFn | None = None,
) -> int:
    an = AnalyticsService(star)
    con = an.connection()
    ch.command("TRUNCATE TABLE IF EXISTS crimetrack_analytics.fact_crimes")
    cur = con.execute(_fact_crimes_sql(an))
    total = 0
    while True:
        chunk = cur.fetch_df_chunk(chunk_vectors)
        if chunk is None or chunk.empty:
            break
        for c in _FACT_STR_COLS:
            chunk[c] = _str(chunk[c]) if c in chunk.columns else ""
        for c in _FACT_INT_COLS:
            chunk[c] = _int(chunk[c]) if c in chunk.columns else 0
        for c in _FACT_SMALL_COLS:
            chunk[c] = _int(chunk[c]) if c in chunk.columns else 0
        ch.insert_df("fact_crimes", chunk)
        total += len(chunk)
        if on_progress:
            on_progress(f"fact_crimes: {total:,} filas".replace(",", "."))
    return total


# --------------------------------------------------------------------------
# Orquestador
# --------------------------------------------------------------------------
def load_all_to_clickhouse(*, on_progress: ProgressFn | None = None) -> dict[str, int]:
    """Carga completa MinIO -> ClickHouse. Devuelve filas por tabla."""
    def log(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    ch = ClickHouseService()
    if not ch.ping():
        raise RuntimeError(
            f"ClickHouse no responde en {ch.host}:{ch.port} (db={ch.database}). "
            "Levanta el perfil analytics: docker compose --profile analytics up -d"
        )

    star = MinioParquetStore()
    tx = TransactionalMinioStore()

    log("Asegurando esquema en ClickHouse…")
    ensure_schema(ch)

    results: dict[str, int] = {}

    log("Cargando dimensiones…")
    results["dim_fecha"] = load_dim_fecha(ch, star)
    results["dim_tipo_crimen"] = load_dim_tipo_crimen(ch, star)
    results["dim_ubicacion"] = load_dim_ubicacion(ch, star)
    results["dim_usuario"] = load_dim_usuario(ch, tx)
    results["dim_patrulla"] = load_dim_patrulla(ch, tx)
    results["dim_estado"] = load_dim_estado(ch, tx)

    log("Cargando hechos operativos…")
    results["fact_incidentes"] = load_fact_incidentes(ch, tx)
    results["fact_expedientes"] = load_fact_expedientes(ch, tx)
    results["fact_evidencias"] = load_fact_evidencias(ch, tx)
    results["fact_auditoria"] = load_fact_auditoria(ch, tx)

    log("Cargando fact_crimes (desnormalizado desde modelo estrella)…")
    results["fact_crimes"] = load_fact_crimes(ch, star, on_progress=on_progress)

    ch.close()
    return results
