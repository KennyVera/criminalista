"""
DAG: dag_minio_to_clickhouse_operational
=========================================
Aterriza las tablas OPERATIVAS (app_*) desde MinIO `datasets/transactional/`
hacia ClickHouse como tablas de staging `stg_*` (mirror crudo, columnas String).

Flujo:
    MinIO datasets/transactional/app_*.parquet
        -> validar existencia de archivos operativos
        -> leer Parquet (pandas/pyarrow)
        -> transformar a String (preserva el dato crudo; el datamart castea)
        -> cargar a ClickHouse stg_* (DROP+CREATE+INSERT = idempotente)

MinIO sigue siendo la base operativa; aquí SOLO se lee de MinIO y se escribe en
ClickHouse. Reejecutar el DAG no genera duplicados (cada tabla se reconstruye).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from crimetrack_etl_common import (
    CH_DB,
    CORE_OPERATIONAL_TABLES,
    OPERATIONAL_TABLES,
    ch_client,
    count_rows,
    land_stg_table,
    object_exists,
    stg_name,
    transactional_key,
)


def validate_operational_files(**_) -> None:
    """
    Verifica los Parquet operativos en MinIO.
    - Tablas CORE faltantes => error (la base operativa no está disponible).
    - Tablas opcionales faltantes => WARN (se tratarán como vacías; algunas se
      materializan de forma perezosa al escribir la primera fila).
    """
    presentes, faltan_core, faltan_opc = [], [], []
    for t in OPERATIONAL_TABLES:
        key = transactional_key(t)
        if object_exists(key):
            presentes.append(t)
            print(f"  [OK] {key}")
        elif t in CORE_OPERATIONAL_TABLES:
            faltan_core.append(t)
            print(f"  [FALTA-CORE] {key}")
        else:
            faltan_opc.append(t)
            print(f"  [FALTA-OPCIONAL] {key} (se tratará como vacía)")

    print(f"Operativos presentes: {len(presentes)}/{len(OPERATIONAL_TABLES)}")
    if faltan_opc:
        print("  [WARN] opcionales no materializadas: " + ", ".join(faltan_opc))
    if faltan_core:
        raise AirflowException(
            "Faltan archivos operativos CORE en MinIO: " + ", ".join(faltan_core)
        )


def land_all_operational(**_) -> None:
    """
    Aterriza TODAS las tablas operativas secuencialmente en una sola tarea.
    Se evita el paralelismo (un proceso por tabla) para no saturar el executor
    en entornos con recursos limitados (Docker Desktop). Una sola conexión a CH.
    """
    client = ch_client()
    client.command(f"CREATE DATABASE IF NOT EXISTS {CH_DB}")
    total = 0
    for app_table in OPERATIONAL_TABLES:
        rows = land_stg_table(client, app_table)
        ver = count_rows(client, stg_name(app_table))
        print(f"LOG carga -> {stg_name(app_table)}: {rows} filas (verificación: {ver}).")
        total += rows
    print(f"Total filas operativas aterrizadas: {total}.")


with DAG(
    dag_id="dag_minio_to_clickhouse_operational",
    description="MinIO datasets/transactional (app_*) -> ClickHouse stg_* (staging operativo).",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["crimetrack", "operational", "minio", "clickhouse"],
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=3),
        "execution_timeout": timedelta(minutes=8),
    },
    max_active_tasks=1,
) as dag:
    validar = PythonOperator(
        task_id="validate_operational_files",
        python_callable=validate_operational_files,
    )

    land = PythonOperator(
        task_id="land_operational_tables",
        python_callable=land_all_operational,
        pool="clickhouse_pool",
    )

    # Encadenamiento: al terminar OK, dispara la construcción del datamart.
    trigger_datamart = TriggerDagRunOperator(
        task_id="trigger_datamart",
        trigger_dag_id="dag_build_crimetrack_datamart",
        wait_for_completion=False,
        reset_dag_run=True,
        trigger_rule="all_success",
    )

    validar >> land >> trigger_datamart
