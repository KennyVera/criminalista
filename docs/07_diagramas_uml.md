# 7. Plano funcional del sistema — CrimeTrack Analytics Corp

**Sistema:** CrimeTrack Analytics Corp (plataforma completa)  
**Estándar:** UML 2.x (vistas de contexto, contenedores, componentes, despliegue, dominio y secuencia)  
**Alcance:** Arquitectura objetivo del producto — capas operativa, analítica, presentación y orquestación.

---

## 7.1 Visión general del sistema

CrimeTrack es una **plataforma de analítica criminal** con arquitectura desacoplada:

| Capa | Tecnología | Función |
|------|------------|---------|
| Presentación | React + Vite + Tailwind | Dashboard, CRUD ISO 9241-210 |
| Aplicación | Django REST | Orquestación, reglas de negocio, ETL |
| Operacional (OLTP) | PocketBase | Modelo estrella: 10 dimensiones + `fact_crimes` |
| Analítica / objetos | MinIO (S3) | Data lake Parquet + evidencias multimedia |
| Orquestación | Docker Compose | MinIO + PocketBase en red `crimetrack_net` |
| Legado (externo) | PostgreSQL | Fuente histórica; migración única hacia PocketBase |

Django **no** persiste datos de crímenes en ORM relacional; consume PocketBase por REST.

```mermaid
flowchart LR
  subgraph operativa [Capa operativa]
    PB[(PocketBase<br/>dims + fact)]
  end
  subgraph analitica [Capa analítica]
    MIN[(MinIO<br/>Parquet + evidencias)]
  end
  subgraph app [Capa aplicación]
    DJ[Django API]
  end
  subgraph ui [Capa presentación]
    WEB[React SPA]
  end

  WEB <--> DJ
  DJ <--> PB
  DJ -->|ETL export| MIN
  PB -->|S3 nativo| MIN
```

---

## 7.2 Diagrama de contexto del sistema (UML — vista Context)

Representa el sistema **CrimeTrack** como caja negra y sus interacciones con actores y sistemas externos.

```mermaid
flowchart TB
  subgraph actores [Actores humanos]
    AN((Analista criminal))
    AD((Administrador de datos))
    SUP((Supervisor táctico))
    ING((Ingeniero / operador ETL))
  end

  subgraph externos [Sistemas externos]
    PG[(PostgreSQL<br/>legado histórico)]
  end

  subgraph sistema [SISTEMA: CrimeTrack Analytics Corp]
    direction TB
    CT[Plataforma integrada<br/>Web + API + datos]
  end

  AN -->|consulta KPIs, mapas, hechos| CT
  AD -->|CRUD dimensiones y hechos| CT
  SUP -->|dashboard ejecutivo| CT
  ING -->|export Parquet, auditoría| CT

  PG -.->|migración única ETL| CT
  CT -->|información para decisiones| AN
  CT -->|información para decisiones| SUP
```

| Interfaz | Descripción |
|----------|-------------|
| UI Web (`:5173`) | Punto único de interacción usuario–sistema |
| API REST (`:8000/api`) | Contrato entre frontend y backend |
| PocketBase (`:8090`) | Persistencia operacional y reglas de colección |
| MinIO (`:9000` / `:9001`) | Almacenamiento objeto S3 (lake + archivos) |

---

## 7.3 Diagrama de contenedores (arquitectura lógica completa)

```mermaid
flowchart TB
  subgraph client [Cliente]
    BROWSER[Navegador web]
  end

  subgraph crimetrack [CrimeTrack Analytics Corp]
    subgraph presentation [Contenedor: Frontend SPA]
      REACT[React Application<br/>Dashboard + CRUD modular]
    end

    subgraph backend [Contenedor: Backend API]
      DJANGO[Django Application<br/>REST + comandos ETL]
    end

    subgraph operational [Contenedor: Base operativa]
      PB[PocketBase Server<br/>Auth + colecciones + API REST]
    end

    subgraph storage [Contenedor: Object Storage]
      MINIO[MinIO Server<br/>API S3 compatible]
    end
  end

  subgraph legacy [Fuente legada — fuera del runtime]
    POSTGRES[(PostgreSQL)]
  end

  BROWSER -->|HTTPS / HTTP| REACT
  REACT -->|JSON /api/*| DJANGO
  DJANGO -->|REST + Admin token| PB
  DJANGO -->|boto3 S3 PUT| MINIO
  PB -->|S3 protocol| MINIO
  POSTGRES -.->|migrate_from_postgres| DJANGO
```

---

## 7.4 Diagrama de componentes (UML — vista Component)

Desglose interno de los contenedores principales.

```mermaid
flowchart TB
  subgraph FE [Frontend — React]
    ROUTER[React Router]
    LAYOUT[DashboardLayout + Sidebar]
    DASH_COMP[Dashboard / KPIs / Recharts]
    CRUD_COMP[CollectionCrud + RecordModal]
    API_CLIENT[api/client.js]
  end

  subgraph BE [Backend — Django]
    URLS[crimetrack.urls]
    VIEWS_API[views_api — CRUD genérico]
    VIEWS_DASH[DashboardStatsView]
    PB_CLIENT[PocketBaseClient]
    META[collections_meta — esquema UI]
    CMD_MIG[migrate_from_postgres]
    CMD_EXP[export_parquet_to_minio]
    CMD_SCHEMA[setup_pocketbase_schema]
  end

  subgraph PB_SYS [PocketBase]
    PB_AUTH[Autenticación superusuarios]
    PB_RULES[Reglas API por colección]
    COL_DIMS[10 × dim_*]
    COL_FACT[fact_crimes]
    COL_RAW[crimes_220k]
  end

  subgraph MINIO_SYS [MinIO]
    BKT_EVID[crimetrack-evidence]
    PATH_PARQ[datasets/parquet/*.parquet]
    PATH_MEDIA[evidencias / thumbs PocketBase]
  end

  ROUTER --> LAYOUT
  LAYOUT --> DASH_COMP
  LAYOUT --> CRUD_COMP
  DASH_COMP --> API_CLIENT
  CRUD_COMP --> API_CLIENT

  API_CLIENT --> URLS
  URLS --> VIEWS_API
  URLS --> VIEWS_DASH
  VIEWS_API --> PB_CLIENT
  VIEWS_API --> META
  VIEWS_DASH --> PB_CLIENT
  CMD_MIG --> PB_CLIENT
  CMD_EXP --> PB_CLIENT
  CMD_EXP --> MINIO_SYS
  CMD_SCHEMA --> PB_CLIENT

  PB_CLIENT --> PB_AUTH
  PB_CLIENT --> COL_DIMS
  PB_CLIENT --> COL_FACT
  PB_CLIENT --> COL_RAW
  PB_AUTH --> PB_RULES
  PB_SYS -->|upload file fields| BKT_EVID
  CMD_EXP --> PATH_PARQ
```

### Inventario de componentes

| Componente | Paquete / ruta | Responsabilidad |
|------------|----------------|-----------------|
| SPA React | `frontend/src/` | Interfaz usuario, usabilidad ISO 9241-210 |
| API REST | `backend_django/core/views_api.py` | Proxy CRUD y estadísticas |
| Cliente PB | `core/services/pocketbase.py` | Integración REST PocketBase |
| Metadatos colecciones | `core/collections_meta.py` | Formularios y menú dinámico |
| ETL legado | `migrate_from_postgres` | Carga inicial desde PostgreSQL |
| ETL analítico | `export_parquet_to_minio` | PB → Parquet → MinIO |
| Bootstrap esquema | `setup_pocketbase_schema` | Creación colecciones dim/fact |
| PocketBase | Docker `:8090` | OLTP, relaciones, ~220k hechos |
| MinIO | Docker `:9000` | Data lake + binarios |

---

## 7.5 Modelo de dominio — modelo estrella (UML — vista de dominio)

```mermaid
erDiagram
  FACT_CRIMES ||--o| DIM_CASO : caso
  FACT_CRIMES ||--o| DIM_TIPO_CRIMEN : tipo_crimen
  FACT_CRIMES ||--o| DIM_UBICACION_LUGAR : ubicacion_lugar
  FACT_CRIMES ||--o| DIM_UBICACION_GEO : ubicacion_geo
  FACT_CRIMES ||--o| DIM_DISTRITO : distrito
  FACT_CRIMES ||--o| DIM_AREA : area
  FACT_CRIMES ||--o| DIM_TIEMPO : tiempo
  FACT_CRIMES ||--o| DIM_ACTUALIZACION : actualizacion
  FACT_CRIMES ||--o| DIM_ARRESTO : arresto
  FACT_CRIMES ||--o| DIM_VIOLENCIA_DOMESTICA : domestico

  FACT_CRIMES {
    string id PK
    int legacy_id
  }
  DIM_CASO {
    string id PK
    string case_number
    string estado_caso
  }
  DIM_TIPO_CRIMEN {
    string id PK
    string primary_type
    string iucr
  }
  DIM_DISTRITO {
    string id PK
    string district
    string beat
  }
  DIM_TIEMPO {
    string id PK
    string date
    string year
  }
```

Colección auxiliar `crimes_220k`: vista plana de staging / consulta masiva sin joins.

---

## 7.6 Diagrama de despliegue (UML — vista Deployment)

Despliegue **del sistema CrimeTrack** en entorno de operación (Docker + servicios de aplicación).

```mermaid
flowchart TB
  subgraph workstation [Nodo: Estación de trabajo / Servidor aplicación]
    subgraph process_fe [Proceso: Frontend]
      NODE[Vite / build estático]
      FE_PORT["«puerto» 5173"]
    end

    subgraph process_be [Proceso: Backend]
      GUNICORN[Django WSGI / runserver]
      BE_PORT["«puerto» 8000"]
      SQLITE[(SQLite<br/>metadatos Django)]
    end

    subgraph docker_host [Motor: Docker Engine]
      subgraph network [Red: crimetrack_net]
        NODE_PB["«contenedor» crimetrack-pocketbase"]
        NODE_MIN["«contenedor» crimetrack-minio"]
      end
      VOL_PB[(Volumen: pocketbase_data)]
      VOL_MIN[(Volumen: minio_data)]
    end
  end

  subgraph users [Actores]
    USER[Usuario final]
  end

  USER --> FE_PORT
  FE_PORT --> NODE
  NODE -->|HTTP /api| BE_PORT
  BE_PORT --> GUNICORN
  GUNICORN --> SQLITE
  GUNICORN -->|TCP 8090| NODE_PB
  GUNICORN -->|TCP 9000| NODE_MIN
  GUNICORN -->|S3 API| NODE_MIN
  NODE_PB -->|S3 interno| NODE_MIN
  NODE_PB --- VOL_PB
  NODE_MIN --- VOL_MIN

  NODE_PB -.- PB_L["«artifact» :8090 Admin + API"]
  NODE_MIN -.- MIN_L["«artifact» :9000 S3 / :9001 Consola"]
```

### Artefactos desplegados

| Nodo / artefacto | Puerto | Rol en el sistema |
|------------------|--------|-------------------|
| `crimetrack-minio` | 9000, 9001 | Object storage S3 |
| `crimetrack-pocketbase` | 8090 | Base operativa + API |
| Django | 8000 | API de negocio y ETL |
| React (Vite) | 5173 | Interfaz web |
| `infra/docker-compose.yml` | — | Orquestación contenedores |

---

## 7.7 Diagrama de actividades — pipeline de datos del sistema

Flujo **completo** de información en CrimeTrack (operación + analítica).

```mermaid
flowchart TD
  START([Inicio operación CrimeTrack])
  A[Usuarios operan vía Web React]
  B{Django API}
  C[Lectura / escritura PocketBase]
  D[(Modelo estrella<br/>dim_* + fact_crimes)]
  E[Adjuntar evidencia multimedia]
  F[(MinIO — bucket evidencias)]
  G{Job ETL programado<br/>export_parquet_to_minio}
  H[Extraer colecciones PB]
  I[Convertir a Parquet]
  J[(MinIO — datasets/parquet)]
  K[Dashboard y CRUD consumen PB]
  END([Decisiones tácticas y operativas])

  START --> A --> B
  B --> C --> D
  C --> E --> F
  D --> G
  G --> H --> I --> J
  D --> K
  J --> K
  K --> END
```

---

## 7.8 Diagramas de secuencia — comportamiento del sistema

### SEC-01 — Consulta de dashboard (operación normal)

```mermaid
sequenceDiagram
  autonumber
  actor Supervisor
  participant React as Frontend React
  participant Django as Django REST API
  participant PB as PocketBase

  Supervisor->>React: Abrir Overview
  React->>Django: GET /api/dashboard/stats/
  Django->>PB: Auth admin + count/list fact_crimes
  PB-->>Django: totales + hechos recientes
  Django-->>React: JSON KPIs + gráficos
  React-->>Supervisor: Render dashboard
```

### SEC-02 — CRUD sobre dimensión (gestión maestros)

```mermaid
sequenceDiagram
  autonumber
  actor Admin as Administrador datos
  participant React as Frontend React
  participant Django as Django REST API
  participant PB as PocketBase

  Admin->>React: Crear / editar dim_distrito_policial
  React->>Django: POST o PATCH /api/collections/{slug}/records/
  Django->>PB: Token admin + validación colección
  PB-->>Django: Registro persistido
  Django-->>React: JSON confirmación
  React-->>Admin: Feedback UI + tabla actualizada
```

### SEC-03 — CRUD hecho delictivo con relaciones (fact_crimes)

```mermaid
sequenceDiagram
  autonumber
  actor Analista
  participant React as Frontend React
  participant Django as Django REST API
  participant PB as PocketBase

  Analista->>React: Alta fact_crimes
  React->>Django: GET options dim_caso, dim_tipo_crimen...
  Django->>PB: Listar registros dimensiones
  PB-->>Django: IDs para selects
  Django-->>React: Opciones relación
  React->>Django: POST fact_crimes + FKs PocketBase
  Django->>PB: create_record + relaciones
  PB-->>Django: Hecho creado
  Django-->>React: 201 Created
  React-->>Analista: Confirmación
```

### SEC-04 — Pipeline analítico PocketBase → Parquet → MinIO

```mermaid
sequenceDiagram
  autonumber
  actor Operador as Operador ETL
  participant Django as Django Command Layer
  participant PB as PocketBase
  participant FS as Sistema archivos
  participant MinIO as MinIO S3

  Operador->>Django: export_parquet_to_minio
  loop Por cada dim_* y fact_crimes
    Django->>PB: GET records paginado
    PB-->>Django: JSON
    Django->>FS: Escribir {coleccion}.parquet
  end
  loop Por cada archivo Parquet
    Django->>MinIO: PUT datasets/parquet/{coleccion}.parquet
    MinIO-->>Django: OK
  end
  Django-->>Operador: Log resumen exportación
```

### SEC-05 — Almacenamiento de evidencia multimedia

```mermaid
sequenceDiagram
  autonumber
  actor Analista
  participant PB as PocketBase
  participant MinIO as MinIO S3

  Analista->>PB: Subir archivo campo File
  PB->>MinIO: PUT objeto S3 crimetrack-evidence/...
  MinIO-->>PB: URL / key almacenada
  PB-->>Analista: Registro con referencia archivo
```

### SEC-06 — Migración legada (proceso de arranque del sistema)

```mermaid
sequenceDiagram
  autonumber
  actor Ingeniero
  participant Django as Django ETL
  participant PG as PostgreSQL legado
  participant PB as PocketBase

  Note over PG,PB: Ejecución única — no forma parte del runtime
  Ingeniero->>Django: migrate_from_postgres
  Django->>PG: SELECT dim_* , fact_crimes
  PG-->>Django: Filas históricas
  Django->>PB: create_record + legacy_id
  PB-->>Django: Modelo estrella poblado
  Django-->>Ingeniero: Sistema listo para operar
```

---

## 7.9 Matriz de trazabilidad — requisitos vs vistas UML

| Requisito académico | Vista UML que lo evidencia |
|---------------------|----------------------------|
| Extraer dataset desde PocketBase | SEC-04, actividad §7.7 |
| Convertir a Parquet | SEC-04, componente `export_parquet_to_minio` |
| Cargar Parquet en MinIO | SEC-04, despliegue MinIO §7.6 |
| Tablas hecho y dimensiones | Modelo dominio §7.5, componente PB |
| CRUD hecho y dimensiones | SEC-02, SEC-03, componente React CRUD |
| Docker | Despliegue §7.6, contenedores §7.3 |
| Arquitectura desacoplada | Contenedores §7.3 (sin ORM Postgres en runtime) |

---

## 7.10 Leyenda y convenciones

| Símbolo / término | Significado |
|-------------------|-------------|
| OLTP | Transacciones operativas en PocketBase |
| Data lake | Capa MinIO con Parquet versionable |
| Django API | Único backend de negocio para la SPA |
| PostgreSQL | Sistema externo; solo migración inicial |
| `crimetrack_net` | Red bridge Docker entre PB y MinIO |

**Documentos relacionados:** `06_empresa_mision_vision_objetivos.md`, `08_casos_de_uso_historias.md`, `00_alineacion_requisitos_1-5.md`.
