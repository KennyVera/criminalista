from django.conf import settings

from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

from rest_framework.response import Response

from rest_framework.views import APIView



from core.collections_meta import ALLOWED_COLLECTIONS, COLLECTIONS, collection_storage

from core.etl.star_schema import run_etl_pb_to_minio
from core.services.faker_realistic import run_realistic_seed_batch
from core.services.faker_seed import (
    MAX_BATCH_SIZE,
    MAX_FACTS_PER_REQUEST,
    run_faker_seed,
    run_faker_seed_batch,
)

from core.services.minio_store import MinioParquetStore, is_minio_collection, is_pocketbase_collection

from core.services.pocketbase import PocketBaseClient, PocketBaseError





def _pb_client() -> PocketBaseClient:

    client = PocketBaseClient()

    client.auth_admin()

    return client





def _minio_store() -> MinioParquetStore:

    return MinioParquetStore()





def _bad_gateway(exc: PocketBaseError) -> Response:

    code = exc.status_code or status.HTTP_502_BAD_GATEWAY

    if code < 400 or code >= 600:

        code = status.HTTP_502_BAD_GATEWAY

    return Response({"error": str(exc), "detail": exc.payload}, status=code)





def _minio_error(exc: Exception) -> Response:

    return Response(

        {"error": str(exc), "detail": "Error leyendo/escribiendo Parquet en MinIO"},

        status=status.HTTP_502_BAD_GATEWAY,

    )





class CollectionsMetaView(APIView):

    authentication_classes = []

    permission_classes = []



    def get(self, request):

        items = []

        for slug, meta in COLLECTIONS.items():

            items.append(

                {

                    "slug": slug,

                    "label": meta["label"],

                    "group": meta.get("group", "dimension"),

                    "storage": meta.get("storage", collection_storage(slug)),

                    "icon": meta.get("icon", "table"),

                    "fields": meta.get("fields", []),

                    "relations": meta.get("relations", []),

                    "read_only_hint": meta.get("read_only_hint", False),

                }

            )

        return Response({"collections": items})





class CollectionMetaDetailView(APIView):

    authentication_classes = []

    permission_classes = []



    def get(self, request, collection: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        meta = dict(COLLECTIONS[collection])

        meta.setdefault("storage", collection_storage(collection))

        return Response(meta)





class DashboardStatsView(APIView):
    """Deprecated: usar /api/packages/dashboard-analitica/overview/"""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "error": "Endpoint movido a /api/packages/dashboard-analitica/overview/",
                "migrate_to": "/api/packages/dashboard-analitica/overview/",
            },
            status=status.HTTP_410_GONE,
        )


class AnalyticsCrimesByDistrictView(APIView):
    """Deprecated: datos incluidos en overview del paquete dashboard_analitica."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "error": "Endpoint movido al paquete dashboard_analitica",
                "migrate_to": "/api/packages/dashboard-analitica/overview/",
            },
            status=status.HTTP_410_GONE,
        )





class CollectionRecordsView(APIView):

    authentication_classes = []

    permission_classes = []



    def get(self, request, collection: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        page = int(request.query_params.get("page", 1))

        per_page = min(int(request.query_params.get("per_page", 20)), 100)

        sort = request.query_params.get("sort", "-id" if is_minio_collection(collection) else "-@rowid")

        filter_query = request.query_params.get("filter") or None

        expand = request.query_params.get("expand") or None

        search = request.query_params.get("search", "").strip()



        if is_minio_collection(collection):

            try:

                store = _minio_store()

                data = store.list_records(

                    collection,

                    page=page,

                    per_page=per_page,

                    sort=sort,

                    search=search or None,

                )

                return Response(data)

            except Exception as exc:

                return _minio_error(exc)



        if search and collection in COLLECTIONS:

            fields = COLLECTIONS[collection].get("fields", [])

            text_fields = [f["name"] for f in fields if f.get("type") == "text"][:3]

            if text_fields:

                parts = [f'{f}~"{{search}}"' for f in text_fields]

                filter_query = " || ".join(parts).replace("{search}", search)



        try:

            with _pb_client() as client:

                data = client.list_records(

                    collection,

                    page=page,

                    per_page=per_page,

                    sort=sort,

                    filter_query=filter_query,

                    expand=expand,

                )

                return Response(data)

        except PocketBaseError as exc:

            return _bad_gateway(exc)



    def post(self, request, collection: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        if is_minio_collection(collection):

            try:

                record = _minio_store().create_record(collection, request.data)

                return Response(record, status=status.HTTP_201_CREATED)

            except Exception as exc:

                return _minio_error(exc)

        try:

            with _pb_client() as client:

                record = client.create_record(collection, request.data)

                return Response(record, status=status.HTTP_201_CREATED)

        except PocketBaseError as exc:

            return _bad_gateway(exc)





class CollectionRecordDetailView(APIView):

    authentication_classes = []

    permission_classes = []



    def get(self, request, collection: str, record_id: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        if is_minio_collection(collection):

            try:

                record = _minio_store().get_record(collection, record_id)

                if record is None:

                    return Response({"error": "No encontrado"}, status=404)

                return Response(record)

            except Exception as exc:

                return _minio_error(exc)

        expand = request.query_params.get("expand") or None

        try:

            with _pb_client() as client:

                return Response(client.get_record(collection, record_id, expand=expand))

        except PocketBaseError as exc:

            return _bad_gateway(exc)



    def patch(self, request, collection: str, record_id: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        if is_minio_collection(collection):

            try:

                record = _minio_store().update_record(collection, record_id, request.data)

                return Response(record)

            except KeyError:

                return Response({"error": "No encontrado"}, status=404)

            except Exception as exc:

                return _minio_error(exc)

        try:

            with _pb_client() as client:

                return Response(client.update_record(collection, record_id, request.data))

        except PocketBaseError as exc:

            return _bad_gateway(exc)



    def delete(self, request, collection: str, record_id: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        if is_minio_collection(collection):

            try:

                _minio_store().delete_record(collection, record_id)

                return Response(status=status.HTTP_204_NO_CONTENT)

            except Exception as exc:

                return _minio_error(exc)

        try:

            with _pb_client() as client:

                client.delete_record(collection, record_id)

                return Response(status=status.HTTP_204_NO_CONTENT)

        except PocketBaseError as exc:

            return _bad_gateway(exc)





class RelationOptionsView(APIView):

    """Opciones para selects de relaciones (fact_crimes) — dimensiones en MinIO."""



    authentication_classes = []

    permission_classes = []



    def get(self, request, collection: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        per_page = min(int(request.query_params.get("per_page", 50)), 100)

        try:

            if is_minio_collection(collection):

                data = _minio_store().list_records(

                    collection, page=1, per_page=per_page, sort="id"

                )

            else:

                with _pb_client() as client:

                    data = client.list_records(

                        collection, page=1, per_page=per_page, sort="legacy_id"

                    )

            options = [

                {

                    "id": item["id"],

                    "label": _option_label(item, collection),

                }

                for item in data.get("items", [])

            ]

            return Response({"options": options, "total": data.get("totalItems", 0)})

        except PocketBaseError as exc:

            return _bad_gateway(exc)

        except Exception as exc:

            return _minio_error(exc)





def _option_label(item: dict, collection: str) -> str:

    for key in (

        "case_number",

        "primary_type",

        "district",

        "ward",

        "domestic",

        "date",

        "legacy_id",

    ):

        if item.get(key) not in (None, ""):

            return f"{key}: {item[key]}"

    rid = item.get("id", "")

    return str(rid)[:24]





def _parse_generate_count(request) -> tuple[int | None, Response | None]:
    count = request.data.get("count")
    if count is None:
        return None, Response(
            {"error": "El campo 'count' es obligatorio"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        count = int(count)
    except (TypeError, ValueError):
        return None, Response(
            {"error": "'count' debe ser un numero entero"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return count, None


@method_decorator(csrf_exempt, name="dispatch")
class GenerateFakeDataView(APIView):
    """POST /api/generate-fake-data/ — encola generación (202 + task_id, no bloquea)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        count, err = _parse_generate_count(request)
        if err:
            return err
        if count < 1 or count > MAX_FACTS_PER_REQUEST:
            return Response(
                {"error": f"'count' debe estar entre 1 y {MAX_FACTS_PER_REQUEST}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.data.get("sync") is True:
            try:
                result = run_faker_seed(count)
                code = (
                    status.HTTP_201_CREATED
                    if result.get("success")
                    else status.HTTP_400_BAD_REQUEST
                )
                return Response(result, status=code)
            except Exception as exc:
                return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        from core.async_jobs import enqueue_faker_job

        payload = enqueue_faker_job(count, realistic=False)
        return Response(
            {
                **payload,
                "message": "Generación en segundo plano. Consulta el estado con task_id.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_exempt, name="dispatch")
class GenerateFakeDataBatchView(APIView):
    """POST /api/generate-fake-data/batch/ — encola lote (máx. 5000 por petición)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        count, err = _parse_generate_count(request)
        if err:
            return err
        if count < 1 or count > MAX_BATCH_SIZE:
            return Response(
                {"error": f"'count' debe estar entre 1 y {MAX_BATCH_SIZE} por lote"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.data.get("sync") is True:
            try:
                result = run_faker_seed_batch(count)
                code = (
                    status.HTTP_201_CREATED
                    if result.get("success")
                    else status.HTTP_400_BAD_REQUEST
                )
                return Response(result, status=code)
            except Exception as exc:
                return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        from core.async_jobs import enqueue_faker_job

        payload = enqueue_faker_job(count, realistic=False)
        return Response({**payload, "batch": True}, status=status.HTTP_202_ACCEPTED)


@method_decorator(csrf_exempt, name="dispatch")
class GenerateFakeDataRealisticBatchView(APIView):
    """POST /api/generate-fake-data/realistic/batch/ — encola lote realista 2001–2026."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        count, err = _parse_generate_count(request)
        if err:
            return err
        if count < 1 or count > MAX_BATCH_SIZE:
            return Response(
                {"error": f"'count' debe estar entre 1 y {MAX_BATCH_SIZE} por lote"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.data.get("sync") is True:
            try:
                result = run_realistic_seed_batch(count)
                code = (
                    status.HTTP_201_CREATED
                    if result.get("success")
                    else status.HTTP_400_BAD_REQUEST
                )
                return Response(result, status=code)
            except Exception as exc:
                return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        from core.async_jobs import enqueue_faker_job

        payload = enqueue_faker_job(count, realistic=True)
        return Response({**payload, "realistic": True, "batch": True}, status=status.HTTP_202_ACCEPTED)


@method_decorator(csrf_exempt, name="dispatch")
class RunEtlToMinioView(APIView):
    """POST /api/etl/pb-to-minio/ — crimes_220k -> dimensiones + fact en MinIO."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from core.services.analytics_service import invalidate_dashboard_cache

        export_raw = request.data.get("export_raw_copy", True)
        try:
            if request.data.get("sync") is True:
                result = run_etl_pb_to_minio(export_raw_copy=bool(export_raw))
                invalidate_dashboard_cache()
                return Response(result, status=status.HTTP_200_OK)

            from core.async_jobs import enqueue_etl_job

            payload = enqueue_etl_job(export_raw_copy=bool(export_raw))
            return Response(
                {
                    **payload,
                    "message": "ETL en segundo plano. Consulta /api/etl-status/<task_id>/",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"error": f"Error en ETL: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class GenerateFakeDataAsyncView(APIView):
    """POST /api/generate-fake-data/async/ — Celery + bulk 5000 (no bloquea Django)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        count, err = _parse_generate_count(request)
        if err:
            return err
        if count < 1 or count > 500_000:
            return Response(
                {"error": "count debe estar entre 1 y 500000"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        realistic = bool(request.data.get("realistic", False))
        from core.async_jobs import enqueue_faker_job

        payload = enqueue_faker_job(count, realistic=realistic)
        return Response(
            {
                **payload,
                "message": "Generación en segundo plano. Consulta el estado con task_id.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class UnifiedJobStatusView(APIView):
    """GET estado unificado (faker, ETL, Celery o hilo en segundo plano)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, task_id: str):
        from core.async_jobs import resolve_job_status

        data = resolve_job_status(task_id)
        return Response(data)


class EtlTaskStatusView(UnifiedJobStatusView):
    """GET /api/etl/status/<task_id>/"""


class EtlStatusAliasView(UnifiedJobStatusView):
    """GET /api/etl-status/<task_id>/ — alias para polling del frontend."""


class GenerateFakeDataTaskStatusView(UnifiedJobStatusView):
    """GET /api/generate-fake-data/status/<task_id>/"""

