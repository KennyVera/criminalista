# 6. Documentación del sistema — CrimeTrack Analytics Corp

## 6.1 Descripción de la empresa

**CrimeTrack Analytics Corp** es una organización de analítica criminal y apoyo a la toma de decisiones en seguridad pública (contexto académico: dataset Chicago Crime / modelo dimensional). Actúa como **centro de inteligencia operativa**: consolida hechos delictivos, dimensiones geográficas, temporales, policiales y judiciales para convertir registros dispersos en **información accionable**.

No vende software como producto final en esta fase; **genera valor** mediante:

- Reducción del tiempo de consulta de patrones delictivos.
- Priorización de recursos (distritos, turnos, tipos de crimen).
- Trazabilidad de casos y actualizaciones (auditoría).

**Stack tecnológico:** PocketBase (datos operativos), MinIO (data lake Parquet + evidencias), Django (API de negocio), React (UI ISO 9241-210), Docker (despliegue local).

---

## 6.2 Misión

> **Transformar datos criminales en conocimiento confiable y oportuno** para que analistas y mandos medios reduzcan incertidumbre, prioricen intervenciones y protejan a la comunidad con decisiones basadas en evidencia.

---

## 6.3 Visión

> Ser la **plataforma de referencia** en analítica criminal integrada, donde cada registro —desde el hecho en calle hasta la dimensión estratégica— alimenta un ecosistema único: **operación en tiempo casi real (PocketBase)** y **analítica escalable en lago de datos (MinIO/Parquet)**, maximizando productividad del personal y margen operativo institucional (más resultados con los mismos recursos).

---

## 6.4 Datos como activo estratégico

En CrimeTrack, **los datos son el activo más valioso**: sin calidad en `fact_crimes` y dimensiones, no hay predicción, no hay despliegue eficiente ni defensa presupuestal. Por ello:

| Principio | Aplicación en CrimeTrack |
|-----------|---------------------------|
| **Una sola fuente de verdad operativa** | PocketBase (colecciones `dim_*`, `fact_crimes`) |
| **Copia analítica inmutable** | Parquet en MinIO (versionable, barata, columnar) |
| **Trazabilidad** | `legacy_id`, `dim_actualizacion`, timestamps |
| **Acceso gobernado** | API Django; no ORM directo a Postgres en producción |

El **margen** no es solo financiero: es **margen de efectividad** (menos horas buscando datos, más horas actuando).

---

## 6.5 Tabla de objetivos estratégicos de la información

| ID | Objetivo estratégico | Necesidad de información — **Táctico** (mandos, analistas) | Necesidad de información — **Operativo** (patrulla, registro) | Alineación productividad / margen |
|----|----------------------|-----------------------------------------------------------|----------------------------------------------------------------|-----------------------------------|
| **OE1** | Reducir tiempo de detección de hotspots | Mapas y rankings por `dim_distrito_policial`, `dim_ubicacion_geografica`, series en `dim_tiempo` | Consulta rápida de `primary_type` y `block` en últimas 24–72 h | Menos tiempo de análisis → más patrullaje dirigido → **mayor detención/previsión por hora** |
| **OE2** | Optimizar asignación de recursos por turno | Cuadros cruzados distrito × `turno` × `primary_type` desde `fact_crimes` | Listado de casos abiertos por `dim_caso.estado_caso` y prioridad | Recursos en el lugar correcto → **menor costo por intervención efectiva** |
| **OE3** | Mejorar calidad y completitud del dato | Indicadores de nulos, duplicados, lag en `dim_actualizacion` | Formularios CRUD con validación en UI (ISO 9241-210) | Datos completos → modelos y reportes confiables → **menos retrabajo** |
| **OE4** | Respaldar decisiones judiciales y de arresto | Historial `dim_arresto`, `dim_violencia_domestica` enlazado al hecho | Captura en campo de flags `arrest`, `domestic` | Menos errores administrativos → **menor riesgo legal/costo** |
| **OE5** | Escalar analítica sin saturar operación | Datasets Parquet en MinIO para BI/ML batch | PocketBase liviano para CRUD y consultas paginadas | Separar OLTP (PB) y analítica (MinIO) → **máximo throughput sin caídas** |
| **OE6** | Auditoría y cumplimiento normativo | Quién actualizó (`usuario_actualizador`, `sistema_origen`) | Registro de evidencias en MinIO vía PocketBase S3 | Trazabilidad → **confianza institucional y continuidad** |

### Cadena de valor (resumen)

```text
Datos crudos → Modelo estrella (PB) → Export Parquet (MinIO) → Dashboards/CRUD
      │                                                              │
      └────────────────── OE3 calidad ──────────────────────────────┘
                              │
                    OE1, OE2 decisiones tácticas/operativas
                              │
                    Máxima productividad + margen operativo
```

---

## 6.6 Actores

| Actor | Rol |
|-------|-----|
| Analista criminal | Consulta, reportes, exportaciones |
| Administrador de datos | CRUD dimensiones, carga Parquet a MinIO |
| Supervisor táctico | Dashboard, KPIs por distrito/tipo |
| Ingeniero de software | Django, Docker, pipelines ETL |
| Docente / auditor | Revisión arquitectura desacoplada |
