"""
DAG: dag_data_quality_checks
============================
Valida la calidad del datamart en ClickHouse y la integridad de la carga
desde MinIO. Pensado para correr DESPUÉS del datamart.

Valida:
  1. Conteo de filas por tabla (y tablas críticas no vacías).
  2. Duplicados (clave `id`) en hechos y dimensiones.
  3. Nulos críticos y campos obligatorios.
  4. Integridad lógica entre tablas (FKs huérfanas, vínculos inválidos).
  5. Errores de carga: conteos ClickHouse vs fuente en MinIO (Parquet).

Cada chequeo registra un reporte claro; los fallos duros levantan
AirflowException, las observaciones se reportan como WARN.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator

from crimetrack_etl_common import (
    CH_DB,
    ch_client,
    count_rows,
    duck_session,
    read_parquet,
    transactional_key,
    BUCKET,
    STAR_PREFIX,
)

TARGET_TABLES = [
    "fact_crimes", "fact_incidentes", "fact_expedientes", "fact_evidencias",
    "fact_auditoria", "dim_fecha", "dim_tipo_crimen", "dim_ubicacion",
    "dim_usuario", "dim_estado", "dim_patrulla",
]
ID_TABLES = TARGET_TABLES  # todas tienen columna id


def _scalar(client, sql: str) -> int:
    try:
        return int(client.command(sql))
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR] {sql} -> {exc}")
        return -1


# 1) Conteo de filas ---------------------------------------------------------
def check_row_counts(**_) -> None:
    client = ch_client()
    print("== Conteo de filas por tabla ==")
    counts = {t: count_rows(client, t) for t in TARGET_TABLES}
    for t, c in counts.items():
        print(f"  {t:18s}: {c}")
    # Crítico: la base estratégica de crímenes debe existir.
    fails = []
    if counts.get("fact_crimes", 0) <= 0:
        fails.append("fact_crimes está vacía (carga estratégica faltante)")
    if counts.get("dim_fecha", 0) <= 0:
        fails.append("dim_fecha está vacía")
    if fails:
        raise AirflowException("Conteos críticos fallidos: " + "; ".join(fails))
    print("OK: conteos de filas válidos.")


# 2) Duplicados --------------------------------------------------------------
def check_duplicates(**_) -> None:
    client = ch_client()
    print("== Duplicados por clave id ==")
    fails = []
    for t in ID_TABLES:
        total = count_rows(client, t)
        if total <= 0:
            continue
        uniques = _scalar(client, f"SELECT uniqExact(id) FROM {CH_DB}.{t}")
        dups = total - uniques
        flag = "OK" if dups == 0 else "DUPLICADOS"
        print(f"  {t:18s}: filas={total} unicos_id={uniques} dups={dups} [{flag}]")
        if dups > 0:
            fails.append(f"{t} ({dups} duplicados)")
    if fails:
        raise AirflowException("Duplicados detectados: " + "; ".join(fails))
    print("OK: sin duplicados.")


# 3) Nulos críticos y campos obligatorios -----------------------------------
def check_nulls_and_mandatory(**_) -> None:
    client = ch_client()
    print("== Nulos críticos / campos obligatorios ==")
    fails = []
    warns = []

    mandatory_id = ["fact_crimes", "fact_incidentes", "fact_expedientes",
                    "fact_evidencias", "fact_auditoria", "dim_usuario"]
    for t in mandatory_id:
        if count_rows(client, t) <= 0:
            continue
        bad = _scalar(client, f"SELECT count() FROM {CH_DB}.{t} WHERE id = 0")
        print(f"  {t:18s}: id=0 -> {bad}")
        if bad > 0:
            fails.append(f"{t} tiene {bad} filas con id=0")

    # Nulos críticos (observaciones, no fallan la corrida)
    if count_rows(client, "fact_crimes") > 0:
        sin_anio = _scalar(client, f"SELECT count() FROM {CH_DB}.fact_crimes WHERE year = 0")
        sin_tipo = _scalar(client, f"SELECT count() FROM {CH_DB}.fact_crimes WHERE primary_type = ''")
        print(f"  fact_crimes: year=0 -> {sin_anio}; primary_type vacío -> {sin_tipo}")
        if sin_anio > 0:
            warns.append(f"fact_crimes: {sin_anio} sin año")
        if sin_tipo > 0:
            warns.append(f"fact_crimes: {sin_tipo} sin tipo")
    if count_rows(client, "fact_incidentes") > 0:
        sin_estado = _scalar(client, f"SELECT count() FROM {CH_DB}.fact_incidentes WHERE estado = ''")
        if sin_estado > 0:
            warns.append(f"fact_incidentes: {sin_estado} sin estado")

    for w in warns:
        print(f"  [WARN] {w}")
    if fails:
        raise AirflowException("Campos obligatorios inválidos: " + "; ".join(fails))
    print("OK: campos obligatorios válidos.")


# 4) Integridad lógica -------------------------------------------------------
def check_logical_integrity(**_) -> None:
    client = ch_client()
    print("== Integridad lógica entre tablas ==")
    warns = []

    if count_rows(client, "fact_incidentes") > 0 and count_rows(client, "fact_expedientes") > 0:
        huerfanos = _scalar(client, f"""
            SELECT count() FROM {CH_DB}.fact_incidentes
            WHERE expediente_case_number != ''
              AND expediente_case_number NOT IN (
                  SELECT case_number FROM {CH_DB}.fact_expedientes
              )
        """)
        print(f"  incidentes con expediente inexistente: {huerfanos}")
        if huerfanos > 0:
            warns.append(f"{huerfanos} incidentes apuntan a un expediente inexistente")

    if count_rows(client, "fact_crimes") > 0 and count_rows(client, "dim_ubicacion") > 0:
        huerfanos = _scalar(client, f"""
            SELECT count() FROM {CH_DB}.fact_crimes
            WHERE fk_distrito != 0
              AND fk_distrito NOT IN (SELECT id FROM {CH_DB}.dim_ubicacion)
        """)
        print(f"  fact_crimes con fk_distrito huérfano: {huerfanos}")
        if huerfanos > 0:
            warns.append(f"{huerfanos} hechos con fk_distrito sin dimensión")

    if count_rows(client, "fact_crimes") > 0 and count_rows(client, "dim_tipo_crimen") > 0:
        huerfanos = _scalar(client, f"""
            SELECT count() FROM {CH_DB}.fact_crimes
            WHERE fk_tipo_crimen != 0
              AND fk_tipo_crimen NOT IN (SELECT id FROM {CH_DB}.dim_tipo_crimen)
        """)
        print(f"  fact_crimes con fk_tipo_crimen huérfano: {huerfanos}")
        if huerfanos > 0:
            warns.append(f"{huerfanos} hechos con fk_tipo_crimen sin dimensión")

    for w in warns:
        print(f"  [WARN] {w}")
    print("OK: chequeo de integridad lógica finalizado.")


# 5) Errores de carga: ClickHouse vs MinIO ----------------------------------
def check_load_completeness(**_) -> None:
    client = ch_client()
    print("== Completitud de carga (ClickHouse vs MinIO) ==")
    fails = []

    pares = [
        ("fact_incidentes", "app_incidentes"),
        ("fact_expedientes", "app_expedientes"),
        ("fact_evidencias", "app_evidencias"),
        ("fact_auditoria", "app_audit_logs"),
    ]
    for ch_table, app_table in pares:
        ch_n = count_rows(client, ch_table)
        src_n = len(read_parquet(transactional_key(app_table)))
        ok = ch_n == src_n
        print(f"  {ch_table:18s}: clickhouse={ch_n} minio={src_n} [{'OK' if ok else 'MISMATCH'}]")
        if not ok:
            fails.append(f"{ch_table}: CH={ch_n} != MinIO={src_n}")

    # fact_crimes vs modelo estrella consolidado
    try:
        con = duck_session()
        src_crimes = int(con.execute(
            f"SELECT count() FROM read_parquet('s3://{BUCKET}/{STAR_PREFIX}/fact_crimes/consolidated/latest.parquet')"
        ).fetchone()[0])
        ch_crimes = count_rows(client, "fact_crimes")
        ok = ch_crimes == src_crimes
        print(f"  fact_crimes        : clickhouse={ch_crimes} minio={src_crimes} [{'OK' if ok else 'MISMATCH'}]")
        if not ok:
            fails.append(f"fact_crimes: CH={ch_crimes} != MinIO={src_crimes}")
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] no se pudo contar fact_crimes en MinIO: {exc}")

    if fails:
        raise AirflowException("Errores de carga (conteos no coinciden): " + "; ".join(fails))
    print("OK: la carga coincide con el origen MinIO.")


with DAG(
    dag_id="dag_data_quality_checks",
    description="Validaciones de calidad del datamart ClickHouse (conteos, duplicados, nulos, integridad, carga).",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["crimetrack", "data-quality", "clickhouse"],
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
        "execution_timeout": timedelta(minutes=8),
    },
    max_active_tasks=1,
) as dag:
    c1 = PythonOperator(task_id="check_row_counts", python_callable=check_row_counts, pool="clickhouse_pool")
    c2 = PythonOperator(task_id="check_duplicates", python_callable=check_duplicates, pool="clickhouse_pool")
    c3 = PythonOperator(task_id="check_nulls_and_mandatory", python_callable=check_nulls_and_mandatory, pool="clickhouse_pool")
    c4 = PythonOperator(task_id="check_logical_integrity", python_callable=check_logical_integrity, pool="clickhouse_pool")
    c5 = PythonOperator(task_id="check_load_completeness", python_callable=check_load_completeness, pool="clickhouse_pool")

    # Secuencial para minimizar procesos concurrentes del executor.
    c1 >> c2 >> c3 >> c4 >> c5
