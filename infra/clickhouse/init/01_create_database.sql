-- =====================================================================
-- CrimeTrack Analytics — Base de datos TÁCTICA / ESTRATÉGICA (OLAP)
-- ---------------------------------------------------------------------
-- ClickHouse es SOLO para análisis táctico/estratégico (lectura).
-- La capa operativa (CRUD) sigue viviendo en MinIO (datasets/transactional/).
-- Airflow es el único responsable de cargar datos MinIO -> ClickHouse.
--
-- Estos scripts corren automáticamente en el PRIMER arranque del contenedor
-- (datadir vacío). Para re-ejecutarlos manualmente:
--   clickhouse-client --user crimetrack --password *** --multiquery < 01_create_database.sql
-- =====================================================================

CREATE DATABASE IF NOT EXISTS crimetrack_analytics;
