"""
DAG: dag_build_crimetrack_datamart
==================================
Construye el DATAMART táctico/estratégico en ClickHouse a partir de:
  * las tablas de staging `stg_*` (cargadas por dag_minio_to_clickhouse_operational)
  * el modelo estrella en MinIO `datasets/star/` (para fact_crimes y sus dims)

Tablas que construye/actualiza (TRUNCATE + INSERT = idempotente, sin duplicados):
  Hechos operativos:  fact_incidentes, fact_expedientes, fact_evidencias, fact_auditoria
  Dimensiones op.:    dim_usuario, dim_patrulla, dim_estado
  Estratégico:        fact_crimes + dim_fecha, dim_tipo_crimen, dim_ubicacion

La transformación de los hechos operativos se hace en SQL (ClickHouse
INSERT ... SELECT desde stg_*), casteando tipos desde el staging crudo.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from crimetrack_etl_common import (
    CH_DB,
    build_fact_crimes,
    build_star_dimensions,
    ch_client,
    count_rows,
    ensure_target_schema,
    table_exists,
)

_TRUE_SQL = "('true','1','yes','si','sí','y','t','verdadero')"


def _require_stg(client, tables: list[str]) -> None:
    faltan = [t for t in tables if not table_exists(client, t)]
    if faltan:
        raise AirflowException(
            "Faltan tablas de staging en ClickHouse: "
            + ", ".join(faltan)
            + ". Ejecuta primero el DAG dag_minio_to_clickhouse_operational."
        )


def ensure_schema(**_) -> None:
    client = ch_client()
    ensure_target_schema(client)
    print(f"Esquema {CH_DB} asegurado.")


def build_operational_facts(**_) -> None:
    client = ch_client()
    _require_stg(client, ["stg_incidentes", "stg_expedientes", "stg_evidencias", "stg_audit_logs"])

    # fact_incidentes
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.fact_incidentes")
    client.command(f"""
        INSERT INTO {CH_DB}.fact_incidentes
            (id, codigo, tipo, prioridad, estado, ubicacion, reportante, fk_patrulla,
             patrulla_codigo, fk_operador, operador_nombre, fk_comisario, comisario_nombre,
             fk_expediente, expediente_case_number, fecha_reporte, fecha_despacho,
             fecha_atendido, fecha_cierre)
        SELECT toUInt64OrZero(id_incidente), codigo, tipo, prioridad, estado, ubicacion,
               reportante, fk_patrulla, patrulla_codigo, fk_operador, operador_nombre,
               fk_comisario, comisario_nombre, fk_expediente, expediente_case_number,
               fecha_reporte, fecha_despacho, fecha_atendido, fecha_cierre
        FROM {CH_DB}.stg_incidentes
    """)

    # fact_expedientes
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.fact_expedientes")
    client.command(f"""
        INSERT INTO {CH_DB}.fact_expedientes
            (id, case_number, fk_caso, titulo, tipo_delito, prioridad, estado, distrito,
             sector, zona, iucr, fbi_code, arresto, violencia_domestica, fecha_hecho,
             creado_en, creador_nombre)
        SELECT toUInt64OrZero(id_expediente), case_number, fk_caso, titulo, tipo_delito,
               prioridad, estado, distrito, sector, zona, iucr, fbi_code,
               if(lower(arresto) IN {_TRUE_SQL}, 1, 0),
               if(lower(violencia_domestica) IN {_TRUE_SQL}, 1, 0),
               fecha_hecho, creado_en, creador_nombre
        FROM {CH_DB}.stg_expedientes
    """)

    # fact_evidencias
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.fact_evidencias")
    client.command(f"""
        INSERT INTO {CH_DB}.fact_evidencias
            (id, fk_caso, tipo_evidencia, nombre_archivo, peso_mb, algoritmo_hash,
             estado_custodia, fk_usuario_carga, fecha_subida)
        SELECT toUInt64OrZero(id_evidencia), fk_caso, tipo_evidencia, nombre_archivo,
               toFloat64OrZero(peso_mb), algoritmo_hash, estado_custodia,
               fk_usuario_carga, fecha_subida
        FROM {CH_DB}.stg_evidencias
    """)

    # fact_auditoria
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.fact_auditoria")
    client.command(f"""
        INSERT INTO {CH_DB}.fact_auditoria
            (id, fk_usuario, accion, tabla_afectada, direccion_ip, fecha_hora)
        SELECT toUInt64OrZero(id_log), fk_usuario, accion, tabla_afectada,
               direccion_ip, fecha_hora
        FROM {CH_DB}.stg_audit_logs
    """)

    for t in ("fact_incidentes", "fact_expedientes", "fact_evidencias", "fact_auditoria"):
        print(f"  {t}: {count_rows(client, t)} filas.")


def build_operational_dims(**_) -> None:
    client = ch_client()
    _require_stg(client, [
        "stg_usuarios", "stg_roles", "stg_patrullas", "stg_expedientes",
        "stg_incidentes", "stg_casos_operativos", "stg_asignaciones", "stg_evidencias",
    ])

    # dim_usuario (join con roles para nombre_rol)
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.dim_usuario")
    client.command(f"""
        INSERT INTO {CH_DB}.dim_usuario
            (id, fk_rol, nombre_rol, numero_placa, nombres, apellidos, email,
             estado_cuenta, fecha_creacion)
        SELECT toUInt64OrZero(u.id_usuario), u.fk_rol, r.nombre_rol, u.numero_placa,
               u.nombres, u.apellidos, u.email, u.estado_cuenta, u.fecha_creacion
        FROM {CH_DB}.stg_usuarios AS u
        LEFT JOIN {CH_DB}.stg_roles AS r ON u.fk_rol = r.id_rol
    """)

    # dim_patrulla
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.dim_patrulla")
    client.command(f"""
        INSERT INTO {CH_DB}.dim_patrulla
            (id, codigo, sector, turno, estado, fk_comisario, comisario_nombre,
             activo, fecha_creacion)
        SELECT toUInt64OrZero(id_patrulla), codigo, sector, turno, estado, fk_comisario,
               comisario_nombre, if(lower(activo) IN {_TRUE_SQL}, 1, 0), fecha_creacion
        FROM {CH_DB}.stg_patrullas
    """)

    # dim_estado (catálogo derivado de estados DISTINCT por ámbito)
    client.command(f"TRUNCATE TABLE IF EXISTS {CH_DB}.dim_estado")
    client.command(f"""
        INSERT INTO {CH_DB}.dim_estado (id, ambito, codigo, descripcion)
        SELECT toUInt32(row_number() OVER (ORDER BY ambito, codigo)) AS id,
               ambito, codigo, '' AS descripcion
        FROM (
            SELECT DISTINCT 'expediente' AS ambito, estado AS codigo
                FROM {CH_DB}.stg_expedientes WHERE estado != ''
            UNION ALL SELECT DISTINCT 'incidente', estado
                FROM {CH_DB}.stg_incidentes WHERE estado != ''
            UNION ALL SELECT DISTINCT 'caso', estado_caso
                FROM {CH_DB}.stg_casos_operativos WHERE estado_caso != ''
            UNION ALL SELECT DISTINCT 'asignacion', estado_asignacion
                FROM {CH_DB}.stg_asignaciones WHERE estado_asignacion != ''
            UNION ALL SELECT DISTINCT 'evidencia', estado_custodia
                FROM {CH_DB}.stg_evidencias WHERE estado_custodia != ''
        )
    """)

    for t in ("dim_usuario", "dim_patrulla", "dim_estado"):
        print(f"  {t}: {count_rows(client, t)} filas.")


def build_strategic_star(**_) -> None:
    client = ch_client()
    dims = build_star_dimensions(client)
    for k, v in dims.items():
        print(f"  {k}: {v} filas.")
    total = build_fact_crimes(client)
    print(f"  fact_crimes: {total} filas.")


with DAG(
    dag_id="dag_build_crimetrack_datamart",
    description="Construye el datamart táctico/estratégico (fact_*/dim_*) en ClickHouse.",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["crimetrack", "datamart", "clickhouse", "olap"],
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=3),
        "execution_timeout": timedelta(minutes=8),
    },
    max_active_tasks=1,
) as dag:
    t_schema = PythonOperator(task_id="ensure_schema", python_callable=ensure_schema)
    t_facts = PythonOperator(task_id="build_operational_facts", python_callable=build_operational_facts, pool="clickhouse_pool")
    t_dims = PythonOperator(task_id="build_operational_dims", python_callable=build_operational_dims, pool="clickhouse_pool")
    t_star = PythonOperator(task_id="build_strategic_star", python_callable=build_strategic_star, pool="clickhouse_pool")

    # Encadenamiento: al terminar OK, dispara las validaciones de calidad.
    trigger_quality = TriggerDagRunOperator(
        task_id="trigger_quality",
        trigger_dag_id="dag_data_quality_checks",
        wait_for_completion=False,
        reset_dag_run=True,
        trigger_rule="all_success",
    )

    # Secuencial (no paralelo) para no saturar el executor en Docker Desktop.
    t_schema >> t_facts >> t_dims >> t_star >> trigger_quality
