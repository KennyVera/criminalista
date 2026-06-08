from django.urls import path

from packages.asignacion_investigaciones.views import (
    AsignarDetectiveView,
    CasosAsignacionView,
    DetectivesDisponiblesView,
    ProgresoInvestigacionView,
    ReasignarDetectiveView,
    RemoverDetectiveView,
)

urlpatterns = [
    path(
        "detectives-disponibles/",
        DetectivesDisponiblesView.as_view(),
        name="asig-detectives-disponibles",
    ),
    path("casos/", CasosAsignacionView.as_view(), name="asig-casos"),
    path("asignar/", AsignarDetectiveView.as_view(), name="asig-asignar"),
    path(
        "casos/<int:fk_caso>/reasignar/",
        ReasignarDetectiveView.as_view(),
        name="asig-reasignar",
    ),
    path(
        "casos/<int:fk_caso>/remover/",
        RemoverDetectiveView.as_view(),
        name="asig-remover",
    ),
    path(
        "progreso/",
        ProgresoInvestigacionView.as_view(),
        name="asig-progreso",
    ),
]
