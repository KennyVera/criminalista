from django.urls import path

from packages.expedientes_criminales.views import (
    ExpedienteBitacoraView,
    ExpedienteCabeceraView,
    ExpedienteDetallesGeneralesView,
    ExpedienteEvidenciasView,
    ExpedienteInformePdfView,
    ExpedienteInvolucradosView,
)

urlpatterns = [
    path(
        "<str:case_number>/",
        ExpedienteCabeceraView.as_view(),
        name="expediente-cabecera",
    ),
    path(
        "<str:case_number>/detalles-generales/",
        ExpedienteDetallesGeneralesView.as_view(),
        name="expediente-detalles",
    ),
    path(
        "<str:case_number>/involucrados/",
        ExpedienteInvolucradosView.as_view(),
        name="expediente-involucrados",
    ),
    path(
        "<str:case_number>/evidencias/",
        ExpedienteEvidenciasView.as_view(),
        name="expediente-evidencias",
    ),
    path(
        "<str:case_number>/bitacora/",
        ExpedienteBitacoraView.as_view(),
        name="expediente-bitacora",
    ),
    path(
        "<str:case_number>/informe-pdf/",
        ExpedienteInformePdfView.as_view(),
        name="expediente-informe-pdf",
    ),
]
