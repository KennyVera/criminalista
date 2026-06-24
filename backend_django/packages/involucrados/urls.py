from django.urls import path

from packages.involucrados.views import (
    InvolucradoBuscarView,
    InvolucradoEditarView,
    InvolucradoFotoView,
    InvolucradoPerfilView,
)

urlpatterns = [
    path("buscar/", InvolucradoBuscarView.as_view(), name="involucrado-buscar"),
    path(
        "<int:id_involucrado>/perfil/",
        InvolucradoPerfilView.as_view(),
        name="involucrado-perfil",
    ),
    path(
        "<int:id_involucrado>/foto/",
        InvolucradoFotoView.as_view(),
        name="involucrado-foto",
    ),
    path(
        "<int:id_involucrado>/",
        InvolucradoEditarView.as_view(),
        name="involucrado-editar",
    ),
]
