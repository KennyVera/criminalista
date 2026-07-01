-- =====================================================================
-- DIMENSIONES (MergeTree) — crimetrack_analytics
-- ---------------------------------------------------------------------
-- Los campos provienen del modelo estrella en MinIO (datasets/star/) y de
-- las tablas operativas en MinIO (datasets/transactional/). Cuando una
-- dimensión consolida varias tablas del origen, se documenta como SUPUESTO.
-- =====================================================================

-- dim_fecha  <-  MinIO star: dim_tiempo (enriquecida)
-- Campos reales: id(legacy), date, year, month, day, hour, day_of_week,
-- quarter, es_fin_de_semana, temporada, turno.
CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_fecha
(
    id                UInt64,
    date              String,
    year              UInt16,
    month             UInt8,
    day               UInt8,
    hour              UInt8,
    day_of_week       String,
    quarter           UInt8,
    es_fin_de_semana  UInt8,
    temporada         String,
    turno             String
)
ENGINE = MergeTree
ORDER BY (id);

-- dim_tipo_crimen  <-  MinIO star: dim_tipo_crimen (enriquecida)
-- Campos reales: id, iucr, primary_type, description, fbi_code,
-- nivel_gravedad, categoria_penal.
CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_tipo_crimen
(
    id              UInt64,
    iucr            String,
    primary_type    String,
    description     String,
    fbi_code        String,
    nivel_gravedad  String,
    categoria_penal String
)
ENGINE = MergeTree
ORDER BY (id);

-- dim_ubicacion  <-  SUPUESTO / CONSOLIDACIÓN
-- En el modelo estrella la ubicación está NORMALIZADA en 4 dimensiones:
--   dim_distrito_policial (district, beat)
--   dim_area_administrativa (ward, community_area)
--   dim_ubicacion_lugar (location_description, block)
--   dim_ubicacion_geografica (latitude, longitude, location)
-- Aquí se consolidan en una sola dimensión analítica. La clave `id`
-- corresponde a dim_distrito_policial.id (es el FK que usa fact_crimes:
-- fk_distrito). Los campos de área/lugar/geo se rellenan por el DAG cuando
-- es posible; si no, quedan vacíos.
CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_ubicacion
(
    id                    UInt64,
    district              String,
    beat                  String,
    nombre_distrito       String,
    ward                  String,   -- SUPUESTO: de dim_area_administrativa
    community_area        String,   -- SUPUESTO: de dim_area_administrativa
    location_description  String,   -- SUPUESTO: de dim_ubicacion_lugar
    block                 String,   -- SUPUESTO: de dim_ubicacion_lugar
    latitude              String,   -- SUPUESTO: de dim_ubicacion_geografica
    longitude             String,   -- SUPUESTO: de dim_ubicacion_geografica
    tipo_zona             String,
    nivel_riesgo          String
)
ENGINE = MergeTree
ORDER BY (id);

-- dim_usuario  <-  MinIO transactional: app_usuarios
-- Campos reales: id_usuario, fk_rol, numero_placa, nombres, apellidos,
-- email, estado_cuenta, fecha_creacion. nombre_rol se resuelve con app_roles
-- en el DAG (SUPUESTO si no se puede cruzar -> vacío).
CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_usuario
(
    id              UInt64,        -- id_usuario
    fk_rol          String,
    nombre_rol      String,        -- SUPUESTO: join app_roles
    numero_placa    String,
    nombres         String,
    apellidos       String,
    email           String,
    estado_cuenta   String,
    fecha_creacion  String
)
ENGINE = MergeTree
ORDER BY (id);

-- dim_estado  <-  SUPUESTO / CATÁLOGO DERIVADO
-- No existe un Parquet "estado" en el origen. Los estados viven como strings
-- en las tablas operativas (app_expedientes.estado, app_incidentes.estado,
-- app_casos_operativos.estado_caso, app_asignaciones.estado_asignacion,
-- app_evidencias.estado_custodia). Esta dimensión es un catálogo que el DAG
-- llena con los valores DISTINCT detectados por ámbito.
CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_estado
(
    id           UInt32,
    ambito       String,   -- expediente | incidente | caso | asignacion | evidencia
    codigo       String,   -- ACTIVO, CERRADO, ARCHIVADO, REABIERTO, ELIMINADO, ...
    descripcion  String
)
ENGINE = MergeTree
ORDER BY (ambito, codigo);

-- dim_patrulla  <-  MinIO transactional: app_patrullas
-- Campos reales: id_patrulla, codigo, sector, turno, estado, fk_comisario,
-- comisario_nombre, activo, fecha_creacion.
CREATE TABLE IF NOT EXISTS crimetrack_analytics.dim_patrulla
(
    id                UInt64,    -- id_patrulla
    codigo            String,
    sector            String,
    turno             String,
    estado            String,
    fk_comisario      String,
    comisario_nombre  String,
    activo            UInt8,
    fecha_creacion    String
)
ENGINE = MergeTree
ORDER BY (id);
