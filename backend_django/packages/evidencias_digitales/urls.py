from django.urls import path

from packages.evidencias_digitales.views import (
    EvidenciaCustodiaOpcionesView,
    EvidenciaCustodiaView,
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
]
