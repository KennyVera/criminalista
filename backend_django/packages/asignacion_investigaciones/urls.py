from django.urls import path

from packages.asignacion_investigaciones.patrullas_views import (
    DespacharView,
    IncidenteApoyoView,
    IncidenteAvanzarView,
    IncidenteCerrarView,
    IncidenteDevolverView,
    IncidenteFinalizarView,
    IncidentesView,
    MisPatrullasView,
    OficialesDisponiblesView,
    PatrullaAsignarOficialesView,
    PatrullaCatalogosView,
    PatrullaOficialDetailView,
    PatrullasView,
)
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
    # ── Operaciones de patrulla (CU-O77 / CU-O78) ──
    path("patrullas/catalogos/", PatrullaCatalogosView.as_view(), name="patrulla-catalogos"),
    path("patrullas/oficiales-disponibles/", OficialesDisponiblesView.as_view(), name="patrulla-oficiales"),
    path("patrullas/", PatrullasView.as_view(), name="patrullas"),
    path(
        "patrullas/<int:fk_patrulla>/oficiales/",
        PatrullaAsignarOficialesView.as_view(),
        name="patrulla-asignar-oficiales",
    ),
    path(
        "patrullas/<int:fk_patrulla>/oficiales/<int:fk_oficial>/",
        PatrullaOficialDetailView.as_view(),
        name="patrulla-oficial-detalle",
    ),
    path("incidentes/", IncidentesView.as_view(), name="incidentes"),
    path("incidentes/<int:fk_incidente>/despachar/", DespacharView.as_view(), name="incidente-despachar"),
    path("incidentes/<int:fk_incidente>/cerrar/", IncidenteCerrarView.as_view(), name="incidente-cerrar"),
    path("incidentes/<int:fk_incidente>/devolver/", IncidenteDevolverView.as_view(), name="incidente-devolver"),
    path("incidentes/<int:fk_incidente>/avanzar/", IncidenteAvanzarView.as_view(), name="incidente-avanzar"),
    path("incidentes/<int:fk_incidente>/finalizar/", IncidenteFinalizarView.as_view(), name="incidente-finalizar"),
    path("incidentes/<int:fk_incidente>/apoyo/", IncidenteApoyoView.as_view(), name="incidente-apoyo"),
    path("mis-patrullas/", MisPatrullasView.as_view(), name="mis-patrullas"),
]
