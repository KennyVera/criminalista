from django.urls import path

from packages.evidencias_digitales.views import (
    EvidenciaCustodiaOpcionesView,
    EvidenciaCustodiaView,
    EvidenciaDescargarView,
    EvidenciaEliminarView,
)

urlpatterns = [
    path(
        "custodia/opciones/",
        EvidenciaCustodiaOpcionesView.as_view(),
        name="evidencias-custodia-opciones",
    ),
    path(
        "<int:id_evidencia>/custodia/",
        EvidenciaCustodiaView.as_view(),
        name="evidencias-custodia",
    ),
    path(
        "<int:id_evidencia>/descargar/",
        EvidenciaDescargarView.as_view(),
        name="evidencias-descargar",
    ),
    path(
        "<int:id_evidencia>/",
        EvidenciaEliminarView.as_view(),
        name="evidencias-eliminar",
    ),
]
