from django.urls import include, path
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.registry import list_packages


class PackagesIndexView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"packages": list_packages()})


urlpatterns = [
    path("", PackagesIndexView.as_view(), name="packages-index"),
    path("autenticacion/", include("packages.autenticacion_seguridad.urls")),
    path("administracion/", include("packages.administracion_sistema.urls")),
    path("auditoria/", include("packages.auditoria_trazabilidad.urls")),
    path("dashboard-analitica/", include("packages.dashboard_analitica.urls")),
    path(
        "asignacion-investigaciones/",
        include("packages.asignacion_investigaciones.urls"),
    ),
    path(
        "expedientes-criminales/",
        include("packages.expedientes_criminales.urls"),
    ),
]
