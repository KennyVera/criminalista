# CrimeTrack — Optimizacion Big Data (4 fases)

## Fase 1: Particionamiento Hive (year/month)

ETL `python manage.py etl_pb_to_minio` escribe hechos en:

```
s3://crimetrack-evidence/datasets/star/fact_crimes/year=2026/month=05/data.parquet
```

## Fase 2: DuckDB + MinIO S3

- `core/services/analytics_service.py`
- Consultas sin cargar todo el dataset en RAM
- Ejemplo API: `GET /api/analytics/crimes-by-district/`

## Fase 3: Redis cache (15 min)

- Contenedor `redis:alpine` en `infra/docker-compose.yml`
- Dashboard: `GET /api/dashboard/stats/` usa cache Redis

## Fase 4: Celery + bulk 5000

- Worker: `celery -A crimetrack worker -l info`
- Docker: `docker compose --profile workers up -d`
- API async: `POST /api/generate-fake-data/async/`
- Progreso: `GET /api/generate-fake-data/status/<task_id>/`
- ETL async: `POST /api/etl/pb-to-minio/` body `{"async": true}`

## Arranque local

```powershell
cd infra
docker compose up -d

cd ..\backend_django
pip install -r requirements.txt
celery -A crimetrack worker -l info
python manage.py runserver
```
