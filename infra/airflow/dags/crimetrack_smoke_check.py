"""
DAG de verificación (fase 1) — NO modifica datos.

Comprueba que Airflow puede:
  1. Conectarse a ClickHouse (capa táctica/estratégica) y leer su versión.
  2. Conectarse a MinIO (capa operativa) y listar objetos del prefijo transaccional.

Es manual (schedule=None) y queda en pausa al crearse. Sirve para validar que la
infraestructura quedó bien levantada antes de construir los pipelines reales.
"""

from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def check_clickhouse() -> None:
    import clickhouse_connect

    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "crimetrack"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )
    version = client.query("SELECT version()").result_rows
    print(f"ClickHouse OK — version: {version}")


def check_minio() -> None:
    import boto3

    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
        aws_access_key_id=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_change_me"),
    )
    bucket = os.getenv("MINIO_BUCKET", "crimetrack-evidence")
    prefix = os.getenv("MINIO_TRANSACTIONAL_PREFIX", "datasets/transactional")
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/", MaxKeys=20)
    keys = [o["Key"] for o in resp.get("Contents", [])]
    print(f"MinIO OK — bucket '{bucket}', objetos en '{prefix}/': {keys}")


with DAG(
    dag_id="crimetrack_smoke_check",
    description="Verifica conectividad Airflow -> MinIO y Airflow -> ClickHouse (read-only).",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["crimetrack", "smoke", "infra"],
) as dag:
    t_clickhouse = PythonOperator(task_id="check_clickhouse", python_callable=check_clickhouse)
    t_minio = PythonOperator(task_id="check_minio", python_callable=check_minio)
    t_clickhouse >> t_minio
