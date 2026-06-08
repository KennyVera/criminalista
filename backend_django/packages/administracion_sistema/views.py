from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAdminJWT, IsAdminOrComisarioJWT
from packages.administracion_sistema.services.backups_admin import BackupsAdminService
from packages.administracion_sistema.services.restore_pipeline import enqueue_restore_and_etl
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
        from packages.autenticacion_seguridad.services.security_policy import (
            validate_politica_value,
        )

        payload = dict(request.data)
        if "valor" in payload:
            svc = TableCrudService("sys_politicas_seguridad")
            current = next(
                (r for r in svc.list_all() if int(r.get("id_politica", -1)) == row_id),
                None,
            )
            clave = str(payload.get("clave") or (current or {}).get("clave", ""))
            try:
                payload["valor"] = validate_politica_value(clave, payload["valor"])
            except ValueError as exc:
                return _err(exc)
        row = TableCrudService("sys_politicas_seguridad").update(row_id, payload)
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
    """CU-17: listar configuraciones y crear nuevas."""

    permission_classes = [IsAdminJWT]

    def get(self, request):
        svc = BackupsAdminService()
        if request.query_params.get("ejecutar_pendientes") == "1":
            svc.run_due_scheduled()
        return Response({"items": svc.get_config()})

    def post(self, request):
        try:
            if request.data.get("accion") == "config":
                row = BackupsAdminService().create_config(request.data)
                return Response(row, status=201)
            config_id = int(request.data.get("id", 1))
            user = getattr(request, "crimetrack_user", {})
            ejecutado = user.get("email") or f"usuario_{user.get('id_usuario', '')}"
            result = BackupsAdminService().run_backup(
                config_id,
                manual=True,
                ejecutado_por=str(ejecutado),
            )
            code = 200 if result.get("success") else 500
            return Response(result, status=code)
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
class AdminRespaldosHistorialView(APIView):
    """HU-4: historial de respaldos con estado y fecha."""

    permission_classes = [IsAdminJWT]

    def get(self, request):
        limit = int(request.query_params.get("limit", 50))
        manual_only = request.query_params.get("manual_only", "1") != "0"
        return Response(
            {"items": BackupsAdminService().list_history(limit=limit, manual_only=manual_only)}
        )

    def post(self, request):
        """Eliminación masiva: { \"accion\": \"eliminar\", \"ids\": [1, 2] }."""
        if str(request.data.get("accion", "")).lower() != "eliminar":
            return Response(
                {"error": "Use accion=eliminar e ids en el cuerpo"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ids = request.data.get("ids") or []
        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": "Indica al menos un id en ids"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(BackupsAdminService().delete_history_bulk(ids))


@method_decorator(csrf_exempt, name="dispatch")
class AdminRespaldoHistorialDetailView(APIView):
    """Elimina un registro del historial (y archivos MinIO asociados)."""

    permission_classes = [IsAdminJWT]

    def delete(self, request, historial_id: int):
        try:
            return Response(BackupsAdminService().delete_history(historial_id))
        except ValueError as exc:
            return _err(exc, 404 if "no encontrado" in str(exc).lower() else 400)
        except Exception as exc:
            return _err(exc, 500)


@method_decorator(csrf_exempt, name="dispatch")
class AdminRespaldosAlertasView(APIView):
    """HU-3: alertas de respaldos fallidos (Comisario + Admin)."""

    permission_classes = [IsAdminOrComisarioJWT]

    def get(self, request):
        hours = int(request.query_params.get("hours", 72))
        return Response({"items": BackupsAdminService().list_failed_alerts(hours=hours)})


@method_decorator(csrf_exempt, name="dispatch")
class AdminRespaldosProgramadosView(APIView):
    """Ejecuta respaldos programados vencidos."""

    permission_classes = [IsAdminJWT]

    def post(self, request):
        results = BackupsAdminService().run_due_scheduled()
        return Response({"ejecutados": len(results), "resultados": results})


@method_decorator(csrf_exempt, name="dispatch")
class AdminRespaldoDescargarView(APIView):
    """Descarga un respaldo como ZIP para guardar en la PC."""

    permission_classes = [IsAdminJWT]

    def get(self, request, historial_id: int):
        try:
            data, filename = BackupsAdminService().build_download_zip(historial_id)
            response = HttpResponse(data, content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Content-Length"] = len(data)
            return response
        except ValueError as exc:
            return _err(exc)
        except Exception as exc:
            return _err(exc, 500)


@method_decorator(csrf_exempt, name="dispatch")
class AdminRespaldoRestaurarView(APIView):
    """Restaura ZIP y ejecuta ETL del modelo estrella automáticamente."""

    permission_classes = [IsAdminJWT]

    def post(self, request):
        upload = request.FILES.get("archivo")
        if not upload:
            return Response(
                {"error": "Envía el archivo ZIP en el campo 'archivo'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not str(upload.name or "").lower().endswith(".zip"):
            return Response(
                {"error": "El archivo debe ser .zip"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = getattr(request, "crimetrack_user", {})
        ejecutado = user.get("email") or f"usuario_{user.get('id_usuario', '')}"
        try:
            task_id = enqueue_restore_and_etl(
                upload.read(),
                ejecutado_por=str(ejecutado),
                export_raw_copy=False,
            )
            return Response(
                {
                    "task_id": task_id,
                    "status": "running",
                    "message": "Restauración y ETL en curso.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as exc:
            return _err(exc, 500)


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
