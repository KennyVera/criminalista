from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.pocketbase import PocketBaseClient, PocketBaseError


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        pb_ok = PocketBaseClient().health()
        return Response(
            {
                "service": "CrimeTrack Analytics Corp API",
                "django": True,
                "pocketbase": pb_ok,
                "pocketbase_url": settings.POCKETBASE_URL,
            }
        )


class FactCrimesListView(APIView):
    """Lista hechos delictivos desde MinIO (Parquet fact_crimes)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from core.services.minio_store import MinioParquetStore

        page = int(request.query_params.get("page", 1))
        per_page = min(int(request.query_params.get("per_page", 20)), 100)

        try:
            data = MinioParquetStore().list_records(
                "fact_crimes",
                page=page,
                per_page=per_page,
                sort="-id",
            )
        except Exception as exc:
            return Response(
                {"error": str(exc), "detail": "MinIO / Parquet no disponible"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(data)
