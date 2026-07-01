-- =====================================================================
-- TABLAS DE HECHOS (MergeTree) — crimetrack_analytics
-- ---------------------------------------------------------------------
-- fact_crimes: DESNORMALIZADO desde el modelo estrella de MinIO
--   (fact_crimes + dim_*), optimizado para OLAP por fecha/zona/tipo.
-- fact_incidentes/expedientes/evidencias/auditoria: derivados de las
--   tablas operativas en MinIO (datasets/transactional/) — solo lectura.
-- =====================================================================

-- fact_crimes  <-  MinIO star: fact_crimes (FKs) JOIN dim_caso, dim_tipo_crimen,
--                  dim_distrito_policial, dim_area_administrativa, dim_tiempo,
--                  dim_ubicacion_lugar, dim_ubicacion_geografica, dim_arresto,
--                  dim_violencia_domestica.
-- Campos reales (tras el join): raw_row_id, case_number, iucr, primary_type,
-- fbi_code, district, beat, ward, community_area, location_description, block,
-- latitude, longitude, date, year, arrest, domestic, estado_caso, prioridad_caso.
CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_crimes
(
    id                    UInt64,
    raw_row_id            String,
    fk_caso               UInt64,
    fk_tipo_crimen        UInt64,
    fk_distrito           UInt64,
    fk_tiempo             UInt64,
    case_number           String,
    iucr                  String,
    primary_type          String,
    fbi_code              String,
    district              String,
    beat                  String,
    ward                  String,
    community_area        String,
    location_description  String,
    block                 String,
    latitude              String,
    longitude             String,
    date                  String,
    year                  UInt16,
    month                 UInt8,
    arrest                UInt8,
    domestic              UInt8,
    estado_caso           String,
    prioridad_caso        String
)
ENGINE = MergeTree
PARTITION BY year
ORDER BY (year, district, primary_type, id);

-- fact_incidentes  <-  MinIO transactional: app_incidentes
-- Campos reales seleccionados para análisis (tipo, prioridad, estado, zona,
-- patrulla, operador, comisario, expediente vinculado, fechas del ciclo).
CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_incidentes
(
    id                      UInt64,    -- id_incidente
    codigo                  String,
    tipo                    String,
    prioridad               String,
    estado                  String,
    ubicacion               String,
    reportante              String,
    fk_patrulla             String,
    patrulla_codigo         String,
    fk_operador             String,
    operador_nombre         String,
    fk_comisario            String,
    comisario_nombre        String,
    fk_expediente           String,
    expediente_case_number  String,
    fecha_reporte           String,
    fecha_despacho          String,
    fecha_atendido          String,
    fecha_cierre            String
)
ENGINE = MergeTree
ORDER BY (estado, id);

-- fact_expedientes  <-  MinIO transactional: app_expedientes
CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_expedientes
(
    id                   UInt64,   -- id_expediente
    case_number          String,
    fk_caso              String,
    titulo               String,
    tipo_delito          String,
    prioridad            String,
    estado               String,
    distrito             String,
    sector               String,
    zona                 String,
    iucr                 String,
    fbi_code             String,
    arresto              UInt8,
    violencia_domestica  UInt8,
    fecha_hecho          String,
    creado_en            String,
    creador_nombre       String
)
ENGINE = MergeTree
ORDER BY (estado, id);

-- fact_evidencias  <-  MinIO transactional: app_evidencias
CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_evidencias
(
    id                UInt64,    -- id_evidencia
    fk_caso           String,
    tipo_evidencia    String,
    nombre_archivo    String,
    peso_mb           Float64,
    algoritmo_hash    String,
    estado_custodia   String,
    fk_usuario_carga  String,
    fecha_subida      String
)
ENGINE = MergeTree
ORDER BY (estado_custodia, id);

-- fact_auditoria  <-  MinIO transactional: app_audit_logs
-- Solo metadatos de evento para análisis (sin payloads ni hashes de cadena).
CREATE TABLE IF NOT EXISTS crimetrack_analytics.fact_auditoria
(
    id               UInt64,    -- id_log
    fk_usuario       String,
    accion           String,
    tabla_afectada   String,
    direccion_ip     String,
    fecha_hora       String
)
ENGINE = MergeTree
ORDER BY (tabla_afectada, id);
