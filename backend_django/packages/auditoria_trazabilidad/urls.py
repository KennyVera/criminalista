from django.urls import path

from packages.auditoria_trazabilidad.views import AuditEventsView, AuditExportView

urlpatterns = [
    path("eventos/", AuditEventsView.as_view(), name="auditoria-eventos"),
    path("eventos/exportar/", AuditExportView.as_view(), name="auditoria-exportar"),
]
