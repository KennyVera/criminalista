# Airflow para CrimeTrack — alineado a la versión de Python del proyecto (3.12).
# Imagen base oficial de Airflow 2.10.x con Python 3.12.
FROM apache/airflow:2.10.3-python3.12

# Dependencias para que los DAGs orquesten MinIO (Parquet) -> ClickHouse.
# Se instalan como usuario airflow (requisito de la imagen oficial).
USER airflow
RUN pip install --no-cache-dir \
    "clickhouse-connect>=0.8,<0.9" \
    "boto3" \
    "s3fs" \
    "pyarrow" \
    "pandas" \
    "duckdb"
