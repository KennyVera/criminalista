from django.urls import path

from packages.estructura_policial.views import (
    DepartamentosView,
    DistritosView,
    EstacionesView,
    PersonalPolicialDetailView,
    PersonalPolicialListCreateView,
    RangosView,
    SeedEstructuraView,
)

urlpatterns = [
    path("departamentos/", DepartamentosView.as_view(), name="org-departamentos"),
    path("distritos/", DistritosView.as_view(), name="org-distritos"),
    path("estaciones/", EstacionesView.as_view(), name="org-estaciones"),
    path("rangos/", RangosView.as_view(), name="org-rangos"),
    path("personal/", PersonalPolicialListCreateView.as_view(), name="org-personal"),
    path(
        "personal/<int:id_personal>/",
        PersonalPolicialDetailView.as_view(),
        name="org-personal-detail",
    ),
    path("seed/", SeedEstructuraView.as_view(), name="org-seed"),
]
