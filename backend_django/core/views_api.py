from django.conf import settings

from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt

from rest_framework import status

from rest_framework.response import Response

from rest_framework.views import APIView



from core.collections_meta import ALLOWED_COLLECTIONS, COLLECTIONS, collection_storage

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





def _collection_label(collection: str) -> str:
    from core.collections_meta import COLLECTIONS

    return (COLLECTIONS.get(collection, {}) or {}).get("label", collection)


def _audit_collection_event(
    request, *, accion: str, collection: str, detalle: str, antes=None, despues=None
) -> None:
    """Audita operaciones CRUD sobre las tablas/datasets genéricos (Explorar tablas)."""
    from packages.shared.audit import client_ip, record_audit

    fk = None
    actor = "Sistema"
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from packages.autenticacion_seguridad.services.auth_service import AuthService

            u = AuthService().me_from_token(auth[7:].strip())
            fk = int(u["id_usuario"])
            actor = (
                f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()
                or u.get("email")
                or "Sistema"
            )
        except Exception:
            fk, actor = None, "Sistema"
    record_audit(
        fk_usuario=fk,
        accion=accion,
        tabla=collection,
        detalle=f"{actor} {detalle}",
        ip=client_ip(request),
        antes=antes,
        despues=despues,
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

                _audit_collection_event(
                    request,
                    accion="RECORD_CREATED",
                    collection=collection,
                    detalle=f"creó un registro en la tabla «{_collection_label(collection)}»",
                    despues=record,
                )

                return Response(record, status=status.HTTP_201_CREATED)

            except Exception as exc:

                return _minio_error(exc)

        try:

            with _pb_client() as client:

                record = client.create_record(collection, request.data)

                _audit_collection_event(
                    request,
                    accion="RECORD_CREATED",
                    collection=collection,
                    detalle=f"creó un registro en la tabla «{_collection_label(collection)}»",
                    despues=record,
                )

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

                store = _minio_store()

                try:

                    antes = store.get_record(collection, record_id)

                except Exception:

                    antes = None

                record = store.update_record(collection, record_id, request.data)

                _audit_collection_event(
                    request,
                    accion="RECORD_UPDATED",
                    collection=collection,
                    detalle=f"actualizó el registro #{record_id} en la tabla «{_collection_label(collection)}»",
                    antes=antes,
                    despues=record,
                )

                return Response(record)

            except KeyError:

                return Response({"error": "No encontrado"}, status=404)

            except Exception as exc:

                return _minio_error(exc)

        try:

            with _pb_client() as client:

                try:

                    antes = client.get_record(collection, record_id)

                except Exception:

                    antes = None

                record = client.update_record(collection, record_id, request.data)

                _audit_collection_event(
                    request,
                    accion="RECORD_UPDATED",
                    collection=collection,
                    detalle=f"actualizó el registro #{record_id} en la tabla «{_collection_label(collection)}»",
                    antes=antes,
                    despues=record,
                )

                return Response(record)

        except PocketBaseError as exc:

            return _bad_gateway(exc)



    def delete(self, request, collection: str, record_id: str):

        if collection not in ALLOWED_COLLECTIONS:

            return Response({"error": "Colección no permitida"}, status=404)

        if is_minio_collection(collection):

            try:

                store = _minio_store()

                try:

                    antes = store.get_record(collection, record_id)

                except Exception:

                    antes = None

                store.delete_record(collection, record_id)

                _audit_collection_event(
                    request,
                    accion="RECORD_DELETED",
                    collection=collection,
                    detalle=f"eliminó el registro #{record_id} de la tabla «{_collection_label(collection)}»",
                    antes=antes,
                )

                return Response(status=status.HTTP_204_NO_CONTENT)

            except Exception as exc:

                return _minio_error(exc)

        try:

            with _pb_client() as client:

                try:

                    antes = client.get_record(collection, record_id)

                except Exception:

                    antes = None

                client.delete_record(collection, record_id)

                _audit_collection_event(
                    request,
                    accion="RECORD_DELETED",
                    collection=collection,
                    detalle=f"eliminó el registro #{record_id} de la tabla «{_collection_label(collection)}»",
                    antes=antes,
                )

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


@method_decorator(csrf_exempt, name="dispatch")
class PocketBaseSyncStatsView(APIView):
    """GET /api/sync/pocketbase/stats/ — conteos PB vs MinIO."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from core.services.pb_sync_service import pocketbase_sync_stats

        try:
            return Response(pocketbase_sync_stats())
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@method_decorator(csrf_exempt, name="dispatch")
class SyncPocketBaseView(APIView):
    """POST /api/sync/pocketbase/ — ETL PocketBase -> MinIO (+ resumen materializado)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from core.cache.invalidation import invalidate_after_etl
        from core.services.pb_sync_service import run_pocketbase_sync

        mode = str(request.data.get("mode", "auto"))
        export_raw = bool(request.data.get("export_raw_copy", True))
        per_page = int(request.data.get("per_page", 500))
        cantidad_registros = request.data.get("cantidad_registros")

        try:
            if request.data.get("sync") is True:
                from core.services.pb_sync_service import validate_cantidad_registros

                parsed_limit = (
                    validate_cantidad_registros(cantidad_registros)
                    if cantidad_registros is not None
                    else None
                )
                result = run_pocketbase_sync(
                    mode=mode,
                    export_raw_copy=export_raw,
                    per_page=per_page,
                    cantidad_registros=parsed_limit,
                )
                invalidate_after_etl(refresh_dashboard=True)
                return Response(result, status=status.HTTP_200_OK)

            from core.async_jobs import enqueue_sync_job
            from core.services.pb_sync_service import validate_cantidad_registros

            parsed_limit = (
                validate_cantidad_registros(cantidad_registros)
                if cantidad_registros is not None
                else None
            )
            payload = enqueue_sync_job(
                mode=mode,
                export_raw_copy=export_raw,
                per_page=per_page,
                cantidad_registros=parsed_limit,
            )
            return Response(
                {
                    **payload,
                    "message": (
                        "Sincronización en segundo plano. "
                        "Consulta /api/jobs/status/<task_id>/"
                    ),
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"error": f"Error en sincronización: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class RunEtlToMinioView(SyncPocketBaseView):
    """POST /api/etl/pb-to-minio/ — alias de sincronización (compatibilidad)."""



class UnifiedJobStatusView(APIView):
    """GET estado unificado (sync/ETL, Celery o hilo en segundo plano)."""

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

