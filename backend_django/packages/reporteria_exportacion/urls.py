from __future__ import annotations

from django.urls import path

from packages.reporteria_exportacion.views import (
    ReportOptionsView,
    ReportScheduleDetailView,
    ReportScheduleListView,
    ReportSendView,
)

urlpatterns = [
    path("opciones/", ReportOptionsView.as_view(), name="reporte-opciones"),
    path("enviar/", ReportSendView.as_view(), name="reporte-enviar"),
    path("programados/", ReportScheduleListView.as_view(), name="reporte-programados"),
    path(
        "programados/<int:schedule_id>/",
        ReportScheduleDetailView.as_view(),
        name="reporte-programado-detalle",
    ),
]
