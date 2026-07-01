"""
crimetrack_etl_common — utilidades compartidas por los DAGs de CrimeTrack.

Arquitectura:
    MinIO datasets/transactional/  --(operational DAG)-->  ClickHouse stg_*
    stg_* (+ MinIO datasets/star/) --(datamart DAG)----->  ClickHouse fact_*/dim_*
    fact_*/dim_*                   --(quality DAG)------>  validaciones

REGLAS:
  * MinIO es la base operativa (solo lectura desde aquí).
  * ClickHouse es SOLO la capa táctica/estratégica (análisis OLAP).
  * Carga idempotente: TRUNCATE/DROP + INSERT para evitar duplicados al reejecutar.

Dependencias (ya incluidas en la imagen de Airflow): boto3, pandas, pyarrow,
duckdb, clickhouse-connect. No se usan dependencias nuevas.
"""

from __future__ import annotations

import io
import os
from typing import Any

import pandas as pd

# --- configuración por entorno (inyectada por docker-compose a Airflow) ----
CH_DB = os.getenv("CLICKHOUSE_DATABASE", os.getenv("CLICKHOUSE_DB", "crimetrack_analytics"))
TX_PREFIX = os.getenv("MINIO_TRANSACTIONAL_PREFIX", "datasets/transactional")
STAR_PREFIX = os.getenv("MINIO_STAR_PREFIX", "datasets/star")
BUCKET = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_change_me")

# Tablas operativas (app_*) que el DAG operativo aterriza como stg_* en ClickHouse.
OPERATIONAL_TABLES = [
    "app_incidentes",
    "app_expedientes",
    "app_evidencias",
    "app_audit_logs",
    "app_usuarios",
    "app_roles",
    "app_patrullas",
    "app_casos_operativos",
    "app_asignaciones",
]

# Núcleo realmente requerido para construir los hechos/dimensiones principales.
# El resto es opcional (puede no estar materializado aún en MinIO -> se trata como vacío).
CORE_OPERATIONAL_TABLES = [
    "app_incidentes",
    "app_expedientes",
    "app_evidencias",
    "app_audit_logs",
    "app_usuarios",
    "app_roles",
    "app_patrullas",
]

# Esquema conocido de cada tabla operativa (espejo de minio_transactional.SCHEMAS).
# Permite crear la stg_* con columnas correctas aunque el Parquet aún no exista
# (las tablas se materializan de forma perezosa cuando se escribe la primera fila).
OPERATIONAL_SCHEMAS: dict[str, list[str]] = {
    "app_roles": ["id_rol", "nombre_rol", "descripcion"],
    "app_usuarios": [
        "id_usuario", "fk_rol", "numero_placa", "nombres", "apellidos", "email",
        "password_hash", "estado_cuenta", "intentos_login_fallidos", "fecha_creacion",
    ],
    "app_evidencias": [
        "id_evidencia", "fk_caso", "fk_usuario_carga", "tipo_evidencia", "nombre_archivo",
        "minio_url", "peso_mb", "hash_sha256", "algoritmo_hash", "estado_custodia",
        "fecha_subida", "fecha_actualizacion_custodia", "fk_usuario_custodia",
    ],
    "app_asignaciones": [
        "id_asignacion", "fk_caso", "case_number", "fk_detective", "detective_nombre",
        "detective_placa", "fk_comisario", "comisario_nombre", "fecha_asignacion",
        "estado_asignacion", "notificado", "fecha_notificacion", "observaciones",
        "fecha_cierre", "motivo_cierre", "estado_caso_snapshot", "prioridad_caso_snapshot",
        "fecha_reporte_snapshot", "observaciones_caso_snapshot", "avance_pct_actual",
    ],
    "app_casos_operativos": [
        "id", "case_number", "estado_caso", "fecha_reporte", "prioridad_caso",
        "investigador_asignado", "indexado_en",
    ],
    "app_audit_logs": [
        "id_log", "fk_usuario", "accion", "tabla_afectada", "detalle", "datos_anteriores",
        "datos_nuevos", "direccion_ip", "fecha_hora", "previous_hash", "event_hash",
    ],
    "app_patrullas": [
        "id_patrulla", "codigo", "sector", "turno", "estado", "fk_comisario",
        "comisario_nombre", "notas", "fecha_creacion", "fecha_actualizacion", "activo",
    ],
    "app_incidentes": [
        "id_incidente", "codigo", "tipo", "descripcion", "ubicacion", "prioridad", "estado",
        "reportante", "fk_patrulla", "patrulla_codigo", "fk_operador", "operador_nombre",
        "fk_comisario", "comisario_nombre", "notas_despacho", "apoyo_solicitado",
        "resultado_atencion", "parte_policial", "motivo_devolucion", "fecha_reporte",
        "fecha_despacho", "fecha_atendido", "fecha_cierre", "fk_expediente",
        "expediente_case_number", "fecha_vinculacion",
    ],
    "app_expedientes": [
        "id_expediente", "case_number", "fk_caso", "titulo", "descripcion", "tipo_delito",
        "ubicacion", "prioridad", "fecha_hecho", "estado", "distrito", "sector", "zona",
        "cuadra", "lugar_hecho", "iucr", "fbi_code", "arresto", "violencia_domestica",
        "fk_creador", "creador_nombre", "creado_en", "actualizado_en", "motivo_estado",
        "fk_autoriza", "autoriza_nombre",
    ],
}


def stg_name(app_table: str) -> str:
    """app_incidentes -> stg_incidentes."""
    return "stg_" + (app_table[4:] if app_table.startswith("app_") else app_table)


# --- conexiones ------------------------------------------------------------
def ch_client():
    import clickhouse_connect

    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "crimetrack"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        database="default",  # se conecta a default; usamos nombres calificados db.tabla
        connect_timeout=10,
        send_receive_timeout=120,  # P5: 2 min máx (antes 300) para no colgar tareas
        compress=True,             # P5: menos tráfico/RAM en transferencias
    )


def s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_KEY,
        aws_secret_access_key=MINIO_SECRET,
    )


def transactional_key(app_table: str) -> str:
    return f"{TX_PREFIX}/{app_table}.parquet"


def star_key(dim: str) -> str:
    return f"{STAR_PREFIX}/{dim}.parquet"


def object_exists(key: str) -> bool:
    try:
        s3_client().head_object(Bucket=BUCKET, Key=key)
        return True
    except Exception:
        return False


def read_parquet(key: str) -> pd.DataFrame:
    try:
        obj = s3_client().get_object(Bucket=BUCKET, Key=key)
        return pd.read_parquet(io.BytesIO(obj["Body"].read()))
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] no se pudo leer s3://{BUCKET}/{key}: {exc}")
        return pd.DataFrame()


def duck_session():
    import duckdb

    endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET s3_url_style='path';")
    con.execute("SET s3_use_ssl=false;")
    con.execute(f"SET s3_endpoint='{endpoint}';")
    con.execute(f"SET s3_access_key_id='{MINIO_KEY}';")
    con.execute(f"SET s3_secret_access_key='{MINIO_SECRET}';")
    con.execute("SET s3_region='us-east-1';")
    return con


# --- coerción de tipos -----------------------------------------------------
_TRUE = {"true", "1", "yes", "si", "sí", "y", "t", "verdadero"}


def to_str(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).replace({"None": "", "nan": ""})


def to_int(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0).astype("int64")


def to_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0.0).astype("float64")


def to_bool(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.lower().isin(_TRUE).astype("uint8")


def prepare(df: pd.DataFrame, spec: list[tuple[str, str, str]]) -> pd.DataFrame:
    out = pd.DataFrame()
    fns = {"str": to_str, "int": to_int, "float": to_float, "bool": to_bool}
    for ch_col, src_col, kind in spec:
        src = df[src_col] if src_col in df.columns else pd.Series([None] * len(df))
        out[ch_col] = fns[kind](src)
    return out


# --- DDL de las tablas analíticas destino ----------------------------------
DDL_DATABASE = f"CREATE DATABASE IF NOT EXISTS {CH_DB}"

DDL_TARGET: dict[str, str] = {
    "dim_fecha": f"CREATE TABLE IF NOT EXISTS {CH_DB}.dim_fecha (id UInt64, date String, year UInt16, month UInt8, day UInt8, hour UInt8, day_of_week String, quarter UInt8, es_fin_de_semana UInt8, temporada String, turno String) ENGINE=MergeTree ORDER BY (id)",
    "dim_tipo_crimen": f"CREATE TABLE IF NOT EXISTS {CH_DB}.dim_tipo_crimen (id UInt64, iucr String, primary_type String, description String, fbi_code String, nivel_gravedad String, categoria_penal String) ENGINE=MergeTree ORDER BY (id)",
    "dim_ubicacion": f"CREATE TABLE IF NOT EXISTS {CH_DB}.dim_ubicacion (id UInt64, district String, beat String, nombre_distrito String, ward String, community_area String, location_description String, block String, latitude String, longitude String, tipo_zona String, nivel_riesgo String) ENGINE=MergeTree ORDER BY (id)",
    "dim_usuario": f"CREATE TABLE IF NOT EXISTS {CH_DB}.dim_usuario (id UInt64, fk_rol String, nombre_rol String, numero_placa String, nombres String, apellidos String, email String, estado_cuenta String, fecha_creacion String) ENGINE=MergeTree ORDER BY (id)",
    "dim_estado": f"CREATE TABLE IF NOT EXISTS {CH_DB}.dim_estado (id UInt32, ambito String, codigo String, descripcion String) ENGINE=MergeTree ORDER BY (ambito, codigo)",
    "dim_patrulla": f"CREATE TABLE IF NOT EXISTS {CH_DB}.dim_patrulla (id UInt64, codigo String, sector String, turno String, estado String, fk_comisario String, comisario_nombre String, activo UInt8, fecha_creacion String) ENGINE=MergeTree ORDER BY (id)",
    "fact_crimes": f"CREATE TABLE IF NOT EXISTS {CH_DB}.fact_crimes (id UInt64, raw_row_id String, fk_caso UInt64, fk_tipo_crimen UInt64, fk_distrito UInt64, fk_tiempo UInt64, case_number String, iucr String, primary_type String, fbi_code String, district String, beat String, ward String, community_area String, location_description String, block String, latitude String, longitude String, date String, year UInt16, month UInt8, arrest UInt8, domestic UInt8, estado_caso String, prioridad_caso String) ENGINE=MergeTree PARTITION BY year ORDER BY (year, district, primary_type, id)",
    "fact_incidentes": f"CREATE TABLE IF NOT EXISTS {CH_DB}.fact_incidentes (id UInt64, codigo String, tipo String, prioridad String, estado String, ubicacion String, reportante String, fk_patrulla String, patrulla_codigo String, fk_operador String, operador_nombre String, fk_comisario String, comisario_nombre String, fk_expediente String, expediente_case_number String, fecha_reporte String, fecha_despacho String, fecha_atendido String, fecha_cierre String) ENGINE=MergeTree ORDER BY (estado, id)",
    "fact_expedientes": f"CREATE TABLE IF NOT EXISTS {CH_DB}.fact_expedientes (id UInt64, case_number String, fk_caso String, titulo String, tipo_delito String, prioridad String, estado String, distrito String, sector String, zona String, iucr String, fbi_code String, arresto UInt8, violencia_domestica UInt8, fecha_hecho String, creado_en String, creador_nombre String) ENGINE=MergeTree ORDER BY (estado, id)",
    "fact_evidencias": f"CREATE TABLE IF NOT EXISTS {CH_DB}.fact_evidencias (id UInt64, fk_caso String, tipo_evidencia String, nombre_archivo String, peso_mb Float64, algoritmo_hash String, estado_custodia String, fk_usuario_carga String, fecha_subida String) ENGINE=MergeTree ORDER BY (estado_custodia, id)",
    "fact_auditoria": f"CREATE TABLE IF NOT EXISTS {CH_DB}.fact_auditoria (id UInt64, fk_usuario String, accion String, tabla_afectada String, direccion_ip String, fecha_hora String) ENGINE=MergeTree ORDER BY (tabla_afectada, id)",
}


def ensure_target_schema(client) -> None:
    client.command(DDL_DATABASE)
    for ddl in DDL_TARGET.values():
        client.command(ddl)


# --- helpers de carga ------------------------------------------------------
def refresh_table(client, table: str, df: pd.DataFrame) -> int:
    """TRUNCATE + INSERT (idempotente). Devuelve filas insertadas."""
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.{table}")
    if df is None or df.empty:
        return 0
    client.insert_df(table, df, database=CH_DB)
    return len(df)


def land_stg_table(client, app_table: str) -> int:
    """
    Aterriza una tabla operativa app_* como stg_* en ClickHouse.
    Todas las columnas como String (preserva el dato crudo); el datamart castea.
    DROP + CREATE + INSERT => idempotente y sincroniza esquema.

    Si el Parquet aún no existe en MinIO (tabla operativa no materializada), se
    crea la stg_* VACÍA con el esquema conocido para no romper el datamart.
    """
    df = read_parquet(transactional_key(app_table))
    table = stg_name(app_table)

    # Columnas: las del Parquet si existen; si no, el esquema conocido.
    cols = list(df.columns) if len(df.columns) > 0 else OPERATIONAL_SCHEMAS.get(app_table, [])
    if not cols:
        print(f"  [WARN] {app_table}: sin columnas ni esquema conocido; se omite.")
        return 0

    cols_ddl = ", ".join(f"`{c}` String" for c in cols)
    client.command(f"DROP TABLE IF EXISTS {CH_DB}.{table}")
    client.command(
        f"CREATE TABLE {CH_DB}.{table} ({cols_ddl}) ENGINE=MergeTree ORDER BY tuple()"
    )
    if df.empty:
        print(f"  {table}: 0 filas (tabla operativa vacía / no materializada).")
        return 0

    str_df = pd.DataFrame({c: to_str(df[c]) for c in cols})
    client.insert_df(table, str_df, database=CH_DB)
    print(f"  {table}: {len(str_df)} filas aterrizadas.")
    return len(str_df)


def table_exists(client, table: str) -> bool:
    row = client.command(f"EXISTS TABLE {CH_DB}.{table}")
    return str(row).strip() in ("1", "True", "true")


def count_rows(client, table: str) -> int:
    try:
        return int(client.command(f"SELECT count() FROM {CH_DB}.{table}"))
    except Exception:
        return -1


# --- dimensiones/hechos del modelo estrella (desde MinIO datasets/star) ----
def _build_dim_fecha_serverside(client) -> int:
    """
    Carga dim_fecha (625k filas) SERVER-SIDE vía s3(), para que el scheduler de
    Airflow (mem_limit 800m) no tenga que cargar el Parquet en pandas. P1/P2.
    """
    src = s3_table(star_key("dim_tiempo"))
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.dim_fecha")
    client.command(f"""
        INSERT INTO {CH_DB}.dim_fecha
            (id, date, year, month, day, hour, day_of_week, quarter,
             es_fin_de_semana, temporada, turno)
        SELECT toUInt64OrZero(toString(id)) AS id, toString(date) AS date,
               toUInt16OrZero(toString(year)) AS year, toUInt8OrZero(toString(month)) AS month,
               toUInt8OrZero(toString(day)) AS day, toUInt8OrZero(toString(hour)) AS hour,
               toString(day_of_week) AS day_of_week, toUInt8OrZero(toString(quarter)) AS quarter,
               if(lower(toString(es_fin_de_semana)) IN {_TRUE_SET}, toUInt8(1), toUInt8(0)) AS es_fin_de_semana,
               toString(temporada) AS temporada, toString(turno) AS turno
        FROM {src}
        SETTINGS max_execution_time = 600
    """)
    return count_rows(client, "dim_fecha")


def build_star_dimensions(client) -> dict[str, int]:
    res: dict[str, int] = {}

    # dim_fecha (grande): server-side; si fallara, fallback a pandas (tolerante).
    try:
        res["dim_fecha"] = _build_dim_fecha_serverside(client)
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] dim_fecha server-side falló ({exc}); fallback a pandas.")
        df = read_parquet(star_key("dim_tiempo"))
        res["dim_fecha"] = refresh_table(client, "dim_fecha", prepare(df, [
            ("id", "id", "int"), ("date", "date", "str"), ("year", "year", "int"),
            ("month", "month", "int"), ("day", "day", "int"), ("hour", "hour", "int"),
            ("day_of_week", "day_of_week", "str"), ("quarter", "quarter", "int"),
            ("es_fin_de_semana", "es_fin_de_semana", "bool"), ("temporada", "temporada", "str"),
            ("turno", "turno", "str"),
        ]))

    df = read_parquet(star_key("dim_tipo_crimen"))
    res["dim_tipo_crimen"] = refresh_table(client, "dim_tipo_crimen", prepare(df, [
        ("id", "id", "int"), ("iucr", "iucr", "str"), ("primary_type", "primary_type", "str"),
        ("description", "description", "str"), ("fbi_code", "fbi_code", "str"),
        ("nivel_gravedad", "nivel_gravedad", "str"), ("categoria_penal", "categoria_penal", "str"),
    ]))

    # dim_ubicacion: clave = dim_distrito_policial.id (FK de fact_crimes.fk_distrito).
    df = read_parquet(star_key("dim_distrito_policial"))
    res["dim_ubicacion"] = refresh_table(client, "dim_ubicacion", prepare(df, [
        ("id", "id", "int"), ("district", "district", "str"), ("beat", "beat", "str"),
        ("nombre_distrito", "nombre_distrito", "str"), ("ward", "__x__", "str"),
        ("community_area", "__x__", "str"), ("location_description", "__x__", "str"),
        ("block", "__x__", "str"), ("latitude", "__x__", "str"), ("longitude", "__x__", "str"),
        ("tipo_zona", "__x__", "str"), ("nivel_riesgo", "__x__", "str"),
    ]))
    return res


def s3_table(key: str) -> str:
    """Expresión de la función de tabla s3() de ClickHouse para un objeto de MinIO."""
    url = f"{MINIO_ENDPOINT}/{BUCKET}/{key}"
    return f"s3('{url}', '{MINIO_KEY}', '{MINIO_SECRET}', 'Parquet')"


_TRUE_SET = "('true','1','yes','si','sí','y','t','verdadero')"


def build_fact_crimes(client) -> int:
    """
    Desnormaliza fact_crimes desde el modelo estrella en MinIO.

    La unión (9 dimensiones) y la inserción se ejecutan SERVER-SIDE en ClickHouse
    vía la función s3() (lee el Parquet directo desde MinIO). Así el contenedor de
    Airflow no carga 733k filas en memoria (evita el cuello de botella de pandas).

    CARGA ATÓMICA (P2): se inserta en una tabla temporal `fact_crimes_tmp` y, solo
    al completar, se intercambia con `fact_crimes` (RENAME). Si Docker/ClickHouse
    se cae a mitad del INSERT, `fact_crimes` queda INTACTA (nunca 0 filas).
    """
    fact = s3_table(f"{STAR_PREFIX}/fact_crimes/consolidated/latest.parquet")

    def dim(name: str) -> str:
        return s3_table(f"{STAR_PREFIX}/{name}.parquet")

    def k(col: str) -> str:  # clave de join normalizada a entero
        return f"toInt64OrZero(toString({col}))"

    # Asegura la tabla destino y prepara una temporal con la MISMA estructura.
    client.command(DDL_TARGET["fact_crimes"])
    client.command(f"DROP TABLE IF EXISTS {CH_DB}.fact_crimes_tmp")
    client.command(f"DROP TABLE IF EXISTS {CH_DB}.fact_crimes_bak")
    client.command(f"CREATE TABLE {CH_DB}.fact_crimes_tmp AS {CH_DB}.fact_crimes")

    sql = f"""
        INSERT INTO {CH_DB}.fact_crimes_tmp
            (id, raw_row_id, fk_caso, fk_tipo_crimen, fk_distrito, fk_tiempo, case_number,
             iucr, primary_type, fbi_code, district, beat, ward, community_area,
             location_description, block, latitude, longitude, date, year, month,
             arrest, domestic, estado_caso, prioridad_caso)
        SELECT
            toUInt64OrZero(toString(f.id)) AS id,
            toString(f.raw_row_id) AS raw_row_id,
            toUInt64OrZero(toString(f.fk_caso)) AS fk_caso,
            toUInt64OrZero(toString(f.fk_tipo_crimen)) AS fk_tipo_crimen,
            toUInt64OrZero(toString(f.fk_distrito)) AS fk_distrito,
            toUInt64OrZero(toString(f.fk_tiempo)) AS fk_tiempo,
            toString(dc.case_number) AS case_number,
            toString(t.iucr) AS iucr, toString(t.primary_type) AS primary_type,
            toString(t.fbi_code) AS fbi_code,
            toString(d.district) AS district, toString(d.beat) AS beat,
            toString(a.ward) AS ward, toString(a.community_area) AS community_area,
            toString(l.location_description) AS location_description, toString(l.block) AS block,
            toString(g.latitude) AS latitude, toString(g.longitude) AS longitude,
            toString(tm.date) AS date,
            if(toUInt16OrZero(toString(tm.year)) BETWEEN 1900 AND 2200,
               toUInt16OrZero(toString(tm.year)), toUInt16(0)) AS year,
            toUInt8OrZero(toString(tm.month)) AS month,
            if(lower(toString(ar.arrest)) IN {_TRUE_SET}, toUInt8(1), toUInt8(0)) AS arrest,
            if(lower(toString(vd.domestic)) IN {_TRUE_SET}, toUInt8(1), toUInt8(0)) AS domestic,
            toString(dc.estado_caso) AS estado_caso, toString(dc.prioridad_caso) AS prioridad_caso
        FROM {fact} AS f
        LEFT JOIN {dim("dim_caso")} AS dc ON {k("f.fk_caso")} = {k("dc.id")}
        LEFT JOIN {dim("dim_tipo_crimen")} AS t ON {k("f.fk_tipo_crimen")} = {k("t.id")}
        LEFT JOIN {dim("dim_distrito_policial")} AS d ON {k("f.fk_distrito")} = {k("d.id")}
        LEFT JOIN {dim("dim_area_administrativa")} AS a ON {k("f.fk_area")} = {k("a.id")}
        LEFT JOIN {dim("dim_tiempo")} AS tm ON {k("f.fk_tiempo")} = {k("tm.id")}
        LEFT JOIN {dim("dim_ubicacion_lugar")} AS l ON {k("f.fk_ubicacion_lugar")} = {k("l.id")}
        LEFT JOIN {dim("dim_ubicacion_geografica")} AS g ON {k("f.fk_ubicacion_geo")} = {k("g.id")}
        LEFT JOIN {dim("dim_arresto")} AS ar ON {k("f.fk_arresto")} = {k("ar.id")}
        LEFT JOIN {dim("dim_violencia_domestica")} AS vd ON {k("f.fk_domestico")} = {k("vd.id")}
        SETTINGS join_use_nulls = 0, max_execution_time = 1200
    """

    # Inserta en la temporal; si esto falla, fact_crimes sigue intacta.
    client.command(sql)

    # Intercambio atómico: tmp -> fact_crimes, fact_crimes -> bak, y se descarta bak.
    client.command(
        f"RENAME TABLE {CH_DB}.fact_crimes TO {CH_DB}.fact_crimes_bak, "
        f"{CH_DB}.fact_crimes_tmp TO {CH_DB}.fact_crimes"
    )
    client.command(f"DROP TABLE IF EXISTS {CH_DB}.fact_crimes_bak")

    total = count_rows(client, "fact_crimes")
    print(f"  fact_crimes: {total} filas (carga atómica server-side vía s3()).")
    return total
