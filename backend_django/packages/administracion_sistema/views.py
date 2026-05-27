from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAdminJWT
from packages.administracion_sistema.services.backups_admin import BackupsAdminService
from packages.administracion_sistema.services.crud_tables import TableCrudService
from packages.administracion_sistema.services.permissions_admin import PermissionsAdminService
from packages.administracion_sistema.services.seed import seed_admin_tables
from packages.administracion_sistema.services.system_status import SystemStatusService
from packages.administracion_sistema.services.users_admin import UsersAdminService
from packages.shared.minio_transactional import TransactionalMinioStore


def _err(exc: Exception, code=400):
    return Response({"error": str(exc)}, status=code)


@method_decorator(csrf_exempt, name="dispatch")
class AdminRolesView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        df = TransactionalMinioStore().read_table("app_roles")
        return Response({"items": df.to_dict(orient="records")})


@method_decorator(csrf_exempt, name="dispatch")
class AdminUsersListCreateView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": UsersAdminService().list_users()})

    def post(self, request):
        try:
            user = UsersAdminService().create_user(request.data)
            fk_rol = int(request.data.get("fk_rol", user["fk_rol"]))
            codigos = request.data.get("permisos", [])
            if codigos:
                PermissionsAdminService().set_role_permissions(fk_rol, codigos)
            return Response(user, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class AdminUserDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request, user_id: int):
        user = UsersAdminService().get_user(user_id)
        if not user:
            return Response({"error": "No encontrado"}, status=404)
        perms = PermissionsAdminService().get_role_permissions(user["fk_rol"])
        return Response({**user, "permisos": perms})

    def patch(self, request, user_id: int):
        try:
            user = UsersAdminService().update_user(user_id, request.data)
            if not user:
                return Response({"error": "No encontrado"}, status=404)
            if "permisos" in request.data:
                PermissionsAdminService().set_role_permissions(
                    user["fk_rol"], request.data["permisos"]
                )
            return Response(user)
        except ValueError as exc:
            return _err(exc)

    def delete(self, request, user_id: int):
        try:
            if UsersAdminService().delete_user(user_id):
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "No encontrado"}, status=404)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class AdminUserStatusView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, user_id: int):
        activa = request.data.get("activa", True)
        user = UsersAdminService().set_account_status(user_id, bool(activa))
        if not user:
            return Response({"error": "No encontrado"}, status=404)
        return Response(user)


@method_decorator(csrf_exempt, name="dispatch")
class AdminPermisosView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": PermissionsAdminService().list_permisos()})


@method_decorator(csrf_exempt, name="dispatch")
class AdminRolPermisosView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request, fk_rol: int):
        return Response(PermissionsAdminService().get_role_permissions(fk_rol))

    def put(self, request, fk_rol: int):
        codigos = request.data.get("codigos", [])
        return Response(PermissionsAdminService().set_role_permissions(fk_rol, codigos))


@method_decorator(csrf_exempt, name="dispatch")
class AdminPoliticasView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": TableCrudService("sys_politicas_seguridad").list_all()})

    def post(self, request):
        row = TableCrudService("sys_politicas_seguridad").create(request.data)
        return Response(row, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class AdminPoliticaDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        row = TableCrudService("sys_politicas_seguridad").update(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        return Response(row)

    def delete(self, request, row_id: int):
        if TableCrudService("sys_politicas_seguridad").delete(row_id):
            return Response(status=204)
        return Response({"error": "No encontrado"}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
class AdminParametrosView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": TableCrudService("sys_parametros").list_all()})

    def post(self, request):
        return Response(TableCrudService("sys_parametros").create(request.data), status=201)


@method_decorator(csrf_exempt, name="dispatch")
class AdminParametroDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        row = TableCrudService("sys_parametros").update(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        return Response(row)


@method_decorator(csrf_exempt, name="dispatch")
class PublicSystemConfigView(APIView):
    """
    Configuración pública de la aplicación (nombre, subtítulo, icono, etc.).

    No requiere autenticación; solo expone parámetros seguros desde sys_parametros.
    """

    authentication_classes = []
    permission_classes: list = []

    def get(self, request):
        rows = TableCrudService("sys_parametros").list_all()
        mapping = {str(r.get("clave")): str(r.get("valor", "")) for r in rows}
        app_name = mapping.get("app_nombre") or "CrimeTrack Analytics"
        subtitle = mapping.get("app_subtitulo") or "Panel de analítica criminal — ISO 9241-210"
        icon_url = mapping.get("app_icon_url") or ""
        return Response(
            {
                "app_nombre": app_name,
                "app_subtitulo": subtitle,
                "app_icon_url": icon_url,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class AdminRespaldosView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": BackupsAdminService().get_config()})

    def post(self, request):
        try:
            result = BackupsAdminService().run_backup(int(request.data.get("id", 1)))
            return Response(result)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class AdminRespaldoDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        row = BackupsAdminService().update_config(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        return Response(row)


@method_decorator(csrf_exempt, name="dispatch")
class AdminCatalogosView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": TableCrudService("sys_catalogo_delitos").list_all()})

    def post(self, request):
        return Response(TableCrudService("sys_catalogo_delitos").create(request.data), status=201)


@method_decorator(csrf_exempt, name="dispatch")
class AdminCatalogoDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        row = TableCrudService("sys_catalogo_delitos").update(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        return Response(row)

    def delete(self, request, row_id: int):
        if TableCrudService("sys_catalogo_delitos").delete(row_id):
            return Response(status=204)
        return Response({"error": "No encontrado"}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
class AdminZonasView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": TableCrudService("sys_zonas_geograficas").list_all()})

    def post(self, request):
        return Response(TableCrudService("sys_zonas_geograficas").create(request.data), status=201)


@method_decorator(csrf_exempt, name="dispatch")
class AdminZonaDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        row = TableCrudService("sys_zonas_geograficas").update(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        return Response(row)

    def delete(self, request, row_id: int):
        if TableCrudService("sys_zonas_geograficas").delete(row_id):
            return Response(status=204)
        return Response({"error": "No encontrado"}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
class AdminEstadoSistemaView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response(SystemStatusService().supervise())


@method_decorator(csrf_exempt, name="dispatch")
class AdminSeedView(APIView):
    permission_classes = [IsAdminJWT]

    def post(self, request):
        from django.conf import settings

        if not settings.DEBUG and not request.data.get("force"):
            return Response({"error": "Solo DEBUG"}, status=403)
        reset = request.data.get("reset", True)
        return Response(seed_admin_tables(reset=reset), status=201)
