from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.cache.redis_cache import cache_response
from packages.autenticacion_seguridad.permissions import IsAdminJWT, IsAdminOrComisarioJWT
from packages.shared.audit import audit_request
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
            plain_password = str(request.data.get("password") or "CrimeTrack2026!")
            user = UsersAdminService().create_user(request.data)
            fk_rol = int(request.data.get("fk_rol", user["fk_rol"]))
            email_sent = False
            email_error = ""
            try:
                from django.conf import settings
                from packages.autenticacion_seguridad.services.email_service import (
                    send_new_user_credentials,
                )

                login_url = getattr(
                    settings,
                    "CRIMETRACK_LOGIN_URL",
                    "http://localhost:5173/login",
                )
                nombre = f"{user.get('nombres', '')} {user.get('apellidos', '')}".strip()
                send_new_user_credentials(
                    to_email=user["email"],
                    nombre=nombre or user["email"],
                    password=plain_password,
                    numero_placa=user.get("numero_placa", ""),
                    nombre_rol=user.get("nombre_rol", ""),
                    login_url=login_url,
                )
                email_sent = True
            except Exception as exc:
                email_error = str(exc)
            audit_request(
                request,
                accion="USER_CREATED",
                tabla="app_usuarios",
                detalle=f"Usuario creado: {user.get('email')} (rol {fk_rol})",
                despues=user,
            )
            payload = {**user, "email_sent": email_sent}
            if email_error:
                payload["email_error"] = email_error
            return Response(payload, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class AdminGeneratePlacaView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        try:
            fk_rol = int(request.query_params.get("fk_rol", 4))
            placa = UsersAdminService().generate_numero_placa(fk_rol)
            return Response({"numero_placa": placa})
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
            antes = UsersAdminService().get_user(user_id)
            user = UsersAdminService().update_user(user_id, request.data)
            if not user:
                return Response({"error": "No encontrado"}, status=404)
            campos = [k for k in request.data.keys() if k not in ("password", "permisos")]
            audit_request(
                request,
                accion="USER_UPDATED",
                tabla="app_usuarios",
                detalle=f"Usuario #{user_id} modificado · campos: {', '.join(campos) or '—'}",
                antes=antes,
                despues=user,
            )
            return Response(user)
        except ValueError as exc:
            return _err(exc)

    def delete(self, request, user_id: int):
        try:
            antes = UsersAdminService().get_user(user_id)
            if UsersAdminService().delete_user(user_id):
                audit_request(
                    request,
                    accion="USER_DELETED",
                    tabla="app_usuarios",
                    detalle=f"Usuario #{user_id} eliminado",
                    antes=antes,
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "No encontrado"}, status=404)
        except ValueError as exc:
            return _err(exc)


@method_decorator(csrf_exempt, name="dispatch")
class AdminUserStatusView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, user_id: int):
        activa = request.data.get("activa", True)
        antes = UsersAdminService().get_user(user_id)
        user = UsersAdminService().set_account_status(user_id, bool(activa))
        if not user:
            return Response({"error": "No encontrado"}, status=404)
        audit_request(
            request,
            accion="USER_STATUS_CHANGED",
            tabla="app_usuarios",
            detalle=f"Usuario #{user_id} → cuenta {'Activa' if activa else 'Inactiva'}",
            antes=antes,
            despues=user,
        )
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
        result = PermissionsAdminService().set_role_permissions(fk_rol, codigos)
        audit_request(
            request,
            accion="ROLE_PERMISSIONS_UPDATED",
            tabla="sys_rol_permisos",
            detalle=f"Rol #{fk_rol} · {len(codigos)} permiso(s) asignado(s)",
        )
        return Response(result)


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
        svc = TableCrudService("sys_politicas_seguridad")
        antes = svc.get(row_id)
        if "valor" in payload:
            clave = str(payload.get("clave") or (antes or {}).get("clave", ""))
            try:
                payload["valor"] = validate_politica_value(clave, payload["valor"])
            except ValueError as exc:
                return _err(exc)
        row = svc.update(row_id, payload)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        audit_request(
            request,
            accion="POLICY_UPDATED",
            tabla="sys_politicas_seguridad",
            detalle=f"Política #{row_id} ({row.get('clave', '')}) actualizada",
            antes=antes,
            despues=row,
        )
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
        row = TableCrudService("sys_parametros").create(request.data)
        audit_request(
            request,
            accion="PARAM_CREATED",
            tabla="sys_parametros",
            detalle=f"Parámetro creado: {row.get('clave', '')}",
            despues=row,
        )
        return Response(row, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class AdminParametroDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        svc = TableCrudService("sys_parametros")
        antes = svc.get(row_id)
        row = svc.update(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        audit_request(
            request,
            accion="PARAM_UPDATED",
            tabla="sys_parametros",
            detalle=f"Parámetro #{row_id} ({row.get('clave', '')}) actualizado",
            antes=antes,
            despues=row,
        )
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
        raw_visible = mapping.get("combobox_opciones_visibles") or "10"
        try:
            combobox_visible = int(raw_visible)
        except (TypeError, ValueError):
            combobox_visible = 10
        combobox_visible = max(3, min(25, combobox_visible))
        return Response(
            {
                "app_nombre": app_name,
                "app_subtitulo": subtitle,
                "app_icon_url": icon_url,
                "combobox_opciones_visibles": combobox_visible,
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
        row = TableCrudService("sys_catalogo_delitos").create(request.data)
        audit_request(
            request,
            accion="CATALOG_CREATED",
            tabla="sys_catalogo_delitos",
            detalle=f"Catálogo de delito creado: {row.get('nombre', row.get('clave', ''))}",
            despues=row,
        )
        return Response(row, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class AdminCatalogoDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        svc = TableCrudService("sys_catalogo_delitos")
        antes = svc.get(row_id)
        row = svc.update(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        audit_request(
            request,
            accion="CATALOG_UPDATED",
            tabla="sys_catalogo_delitos",
            detalle=f"Catálogo de delito #{row_id} actualizado",
            antes=antes,
            despues=row,
        )
        return Response(row)

    def delete(self, request, row_id: int):
        svc = TableCrudService("sys_catalogo_delitos")
        antes = svc.get(row_id)
        if svc.delete(row_id):
            audit_request(
                request,
                accion="CATALOG_DELETED",
                tabla="sys_catalogo_delitos",
                detalle=f"Catálogo de delito #{row_id} eliminado",
                antes=antes,
            )
            return Response(status=204)
        return Response({"error": "No encontrado"}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
class AdminZonasView(APIView):
    permission_classes = [IsAdminJWT]

    def get(self, request):
        return Response({"items": TableCrudService("sys_zonas_geograficas").list_all()})

    def post(self, request):
        row = TableCrudService("sys_zonas_geograficas").create(request.data)
        audit_request(
            request,
            accion="ZONE_CREATED",
            tabla="sys_zonas_geograficas",
            detalle=f"Zona geográfica creada: {row.get('nombre', '')}",
            despues=row,
        )
        return Response(row, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class AdminZonaDetailView(APIView):
    permission_classes = [IsAdminJWT]

    def patch(self, request, row_id: int):
        svc = TableCrudService("sys_zonas_geograficas")
        antes = svc.get(row_id)
        row = svc.update(row_id, request.data)
        if not row:
            return Response({"error": "No encontrado"}, status=404)
        audit_request(
            request,
            accion="ZONE_UPDATED",
            tabla="sys_zonas_geograficas",
            detalle=f"Zona geográfica #{row_id} actualizada",
            antes=antes,
            despues=row,
        )
        return Response(row)

    def delete(self, request, row_id: int):
        svc = TableCrudService("sys_zonas_geograficas")
        antes = svc.get(row_id)
        if svc.delete(row_id):
            audit_request(
                request,
                accion="ZONE_DELETED",
                tabla="sys_zonas_geograficas",
                detalle=f"Zona geográfica #{row_id} eliminada",
                antes=antes,
            )
            return Response(status=204)
        return Response({"error": "No encontrado"}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
class AdminEstadoSistemaView(APIView):
    permission_classes = [IsAdminJWT]

    @staticmethod
    def _admin_status_key(request, *args, **kwargs) -> str:
        return "estado-sistema"

    @cache_response("admin:estado", ttl=120, key_builder=_admin_status_key)
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
