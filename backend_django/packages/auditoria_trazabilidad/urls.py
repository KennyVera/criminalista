from django.urls import path

from packages.auditoria_trazabilidad.views import (
    AuditEventsView,
    AuditExportView,
    AuditIntegrityView,
    CustodyIntegrityView,
)

urlpatterns = [
    path("eventos/", AuditEventsView.as_view(), name="auditoria-eventos"),
    path("eventos/exportar/", AuditExportView.as_view(), name="auditoria-exportar"),
    path("integridad/", AuditIntegrityView.as_view(), name="auditoria-integridad"),
    path("custodia/", CustodyIntegrityView.as_view(), name="auditoria-custodia"),
]
