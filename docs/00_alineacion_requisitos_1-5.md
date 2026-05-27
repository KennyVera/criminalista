# Alineación requisitos 1–5 vs implementación actual

**Proyecto:** CrimeTrack Analytics Corp  
**Arquitectura (corregida por ingeniero):** Django (API) + PocketBase (solo raw) + MinIO (modelo estrella Parquet) + Docker

---

## Matriz de cumplimiento

| # | Requisito del ingeniero | Implementación | ¿Cumple? |
|---|-------------------------|----------------|----------|
| **1** | Extraer dataset **desde PocketBase** | `etl_pb_to_minio` / `export_parquet_to_minio` leen `crimes_220k` vía API REST | **Sí** |
| **2** | Convertir a **Parquet** | `pandas` + `pyarrow` en el ETL | **Sí** |
| **3** | Cargar Parquet en **MinIO** | `MinioParquetStore` → `datasets/star/{coleccion}.parquet` | **Sí** |
| **4** | Tabla de hechos y dimensiones | Generadas en ETL desde raw; persistidas en MinIO | **Sí** |
| **5** | CRUD hecho + dimensiones | React + Django → MinIO (dims/fact); raw → PocketBase | **Sí** |

---

## Flujo ETL (1→3)

```text
PostgreSQL (migración única, opcional)
        │
        ▼  migrate_from_postgres --steps raw
PocketBase: crimes_220k  (~220k filas, ÚNICA colección de negocio)
        │
        ▼  [1] Extracción API REST
   DataFrame pandas
        │
        ▼  [2] Transformación modelo estrella + Parquet
   dim_*.parquet, fact_crimes.parquet
        │
        ▼  [3] Upload S3 → MinIO
MinIO: datasets/star/  (capa analítica asignada al equipo)
        │
        ▼
Django API + React CRUD (dims/fact desde MinIO; raw desde PB)
```

---

## Comandos

```powershell
cd backend_django
.\venv\Scripts\Activate.ps1

# 1. Solo crimes_220k en PocketBase (si vienes de Postgres)
python manage.py setup_pocketbase_schema
python manage.py migrate_from_postgres --steps raw

# 2. Limpiar dims/fact antiguas de PocketBase (una vez)
python manage.py cleanup_pocketbase_dims

# 3. ETL completo → MinIO
python manage.py etl_pb_to_minio
# alias: python manage.py export_parquet_to_minio
```

---

## Mensaje para el informe

> «PocketBase aloja únicamente el **dataset crudo** (`crimes_220k`, ~220k registros).  
> El **modelo estrella** (10 dimensiones + `fact_crimes`) se materializa mediante **ETL** en archivos **Parquet** en **MinIO** (data lake del equipo).  
> Django enruta el CRUD: raw → PocketBase; analítico → MinIO.  
> PostgreSQL se usó una sola vez para la carga inicial; no forma parte del runtime.»
