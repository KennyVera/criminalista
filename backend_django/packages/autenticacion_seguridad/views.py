from __future__ import annotations

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAdminJWT, IsAuthenticatedJWT
from packages.autenticacion_seguridad.services.auth_service import AuthError, AuthService
from packages.autenticacion_seguridad.services.jwt_tokens import decode_access_token
from packages.autenticacion_seguridad.services.password_recovery import PasswordRecoveryService
from packages.autenticacion_seguridad.services.profile_service import ProfileService
from packages.shared.audit import audit_request


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _user_agent(request) -> str:
    return request.META.get("HTTP_USER_AGENT", "")[:500]


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        if not email or not password:
            return Response(
                {"error": "email y password son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = AuthService().login(
                email,
                password,
                ip=_client_ip(request),
                user_agent=_user_agent(request),
            )
            return Response(result, status=status.HTTP_200_OK)
        except AuthError as exc:
            code = getattr(exc, "code", "AUTH_ERROR")
            http_status = (
                status.HTTP_503_SERVICE_UNAVAILABLE
                if code == "SYSTEM_RECOVERY"
                else status.HTTP_401_UNAUTHORIZED
            )
            return Response(
                {"error": str(exc), "code": code},
                status=http_status,
            )


@method_decorator(csrf_exempt, name="dispatch")
class MfaVerifyView(APIView):
    """POST — completa el inicio de sesión validando el código 2FA enviado por correo."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        code = request.data.get("code", "").strip()
        if not email or not code:
            return Response(
                {"error": "email y code son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = AuthService().verify_login_mfa(
                email,
                code,
                ip=_client_ip(request),
                user_agent=_user_agent(request),
            )
            return Response(result, status=status.HTTP_200_OK)
        except AuthError as exc:
            return Response(
                {"error": str(exc), "code": getattr(exc, "code", "AUTH_ERROR")},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@method_decorator(csrf_exempt, name="dispatch")
class MfaResendView(APIView):
    """POST — reenvía el código 2FA si hay una verificación en curso."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response(
                {"error": "email es obligatorio"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            result = AuthService().resend_login_mfa(email, ip=_client_ip(request))
            return Response(result, status=status.HTTP_200_OK)
        except AuthError as exc:
            return Response(
                {"error": str(exc), "code": getattr(exc, "code", "AUTH_ERROR")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {"error": f"No se pudo enviar el correo: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def post(self, request):
        user = getattr(request, "crimetrack_user", None)
        jti = None
        token = getattr(request, "crimetrack_token", None)
        if token:
            try:
                jti = decode_access_token(token).get("jti")
            except Exception:
                pass
        if user:
            AuthService().logout(
                int(user["id_usuario"]),
                ip=_client_ip(request),
                jti=str(jti) if jti else None,
                email=str(user.get("email", "")),
                user_agent=_user_agent(request),
            )
        return Response({"message": "Sesión cerrada"}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class ChangePasswordView(APIView):
    """POST — cambia la contraseña del usuario autenticado."""

    permission_classes = [IsAuthenticatedJWT]

    def post(self, request):
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")
        if not current_password or not new_password:
            return Response(
                {"error": "current_password y new_password son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.crimetrack_user
        try:
            result = AuthService().change_password(
                int(user["id_usuario"]),
                str(current_password),
                str(new_password),
                ip=_client_ip(request),
            )
            return Response(result, status=status.HTTP_200_OK)
        except AuthError as exc:
            return Response(
                {"error": str(exc), "code": getattr(exc, "code", "AUTH_ERROR")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class ProfileView(APIView):
    """GET/PATCH — perfil del usuario autenticado."""

    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        user_id = int(request.crimetrack_user["id_usuario"])
        profile = ProfileService().get_profile(user_id)
        if not profile:
            return Response({"error": "No encontrado"}, status=404)
        return Response(profile)

    def patch(self, request):
        user_id = int(request.crimetrack_user["id_usuario"])
        try:
            antes = ProfileService().get_profile(user_id)
            profile = ProfileService().update_profile(user_id, request.data)
            audit_request(
                request,
                accion="PROFILE_UPDATED",
                tabla="app_perfiles_usuario",
                detalle=f"Perfil actualizado: {profile.get('email', '')}",
                antes=antes,
                despues=profile,
            )
            return Response(profile)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class ProfileFotoView(APIView):
    """GET — foto de perfil. POST — subir foto. DELETE — quitar foto."""

    permission_classes = [IsAuthenticatedJWT]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        user_id = int(request.crimetrack_user["id_usuario"])
        foto = ProfileService().get_foto(user_id)
        if not foto:
            return Response({"error": "Sin foto de perfil"}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(foto["body"], content_type=foto["content_type"])
        response["Cache-Control"] = "private, no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        return response

    def post(self, request):
        user_id = int(request.crimetrack_user["id_usuario"])
        archivo = request.FILES.get("foto") or request.FILES.get("archivo")
        if not archivo:
            return Response(
                {"error": "Campo 'foto' requerido (multipart)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            profile = ProfileService().set_foto(
                user_id,
                file_obj=archivo,
                filename=str(archivo.name or "foto.jpg"),
            )
            audit_request(
                request,
                accion="PROFILE_PHOTO_UPDATED",
                tabla="app_perfiles_usuario",
                detalle=f"Foto de perfil actualizada: {profile.get('email', '')}",
            )
            return Response(profile)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user_id = int(request.crimetrack_user["id_usuario"])
        profile = ProfileService().remove_foto(user_id)
        audit_request(
            request,
            accion="PROFILE_PHOTO_REMOVED",
            tabla="app_perfiles_usuario",
            detalle=f"Foto de perfil eliminada: {profile.get('email', '')}",
        )
        return Response(profile)


@method_decorator(csrf_exempt, name="dispatch")
class MeView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        user_id = int(request.crimetrack_user["id_usuario"])
        profile = ProfileService().get_profile(user_id)
        if not profile:
            return Response({"error": "No encontrado"}, status=404)
        permisos = []
        try:
            from packages.autenticacion_seguridad.services.permisos_operativos_service import (
                PermisosOperativosService,
            )

            permisos = PermisosOperativosService().list_rol_permisos(int(profile["fk_rol"]))
        except Exception:
            pass
        personal = None
        try:
            from packages.estructura_policial.services.personal_service import PersonalPolicialService

            personal = PersonalPolicialService().get_by_usuario(user_id)
        except Exception:
            pass
        return Response({"user": profile, "permisos": permisos, "personal_policial": personal})


@method_decorator(csrf_exempt, name="dispatch")
class RolesListView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        return Response({"roles": AuthService().list_roles()})


@method_decorator(csrf_exempt, name="dispatch")
class ActiveSessionsListView(APIView):
    """GET — dataset de sesiones activas (solo Admin)."""

    permission_classes = [IsAdminJWT]

    def get(self, request):
        sessions = AuthService().list_active_sessions()
        return Response(
            {
                "total": len(sessions),
                "items": sessions,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CloseActiveSessionView(APIView):
    """POST — cierra una sesión activa (solo Admin)."""

    permission_classes = [IsAdminJWT]

    def post(self, request, id_sesion: int):
        admin = request.crimetrack_user
        admin_nombre = f"{admin.get('nombres', '')} {admin.get('apellidos', '')}".strip()
        try:
            result = AuthService().admin_close_session(
                id_sesion,
                admin_id=int(admin["id_usuario"]),
                admin_nombre=admin_nombre,
                ip=_client_ip(request),
            )
            return Response(result)
        except AuthError as exc:
            return Response(
                {"error": str(exc), "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )


@method_decorator(csrf_exempt, name="dispatch")
class SessionStatusView(APIView):
    """GET — valida si la sesión del token sigue activa (polling cliente)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return Response({"valid": False, "code": "NO_TOKEN"})
        token = auth[7:].strip()
        try:
            return Response(AuthService().session_status_from_token(token))
        except AuthError as exc:
            return Response(
                {"valid": False, "code": exc.code, "message": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@method_decorator(csrf_exempt, name="dispatch")
class RequestPasswordResetView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response({"error": "email es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = PasswordRecoveryService().request_code(email)
            return Response(result, status=status.HTTP_200_OK)
        except AuthError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"error": f"No se pudo enviar el correo: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


@method_decorator(csrf_exempt, name="dispatch")
class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        code = request.data.get("code", "").strip()
        new_password = request.data.get("new_password", "")
        if not email or not code or not new_password:
            return Response(
                {"error": "email, code y new_password son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = PasswordRecoveryService().reset_password(email, code, new_password)
            return Response(result, status=status.HTTP_200_OK)
        except AuthError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class SeedAuthView(APIView):
    """POST — recrea tablas y usuario demo (solo desarrollo)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from django.conf import settings

        if not settings.DEBUG:
            return Response({"error": "Solo en DEBUG"}, status=status.HTTP_403_FORBIDDEN)
        from packages.autenticacion_seguridad.services.seed import seed_auth_data

        result = seed_auth_data(reset=True)
        return Response(result, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class PermisosListView(APIView):
    """GET — catálogo de permisos operativos (app_permisos)."""

    permission_classes = [IsAdminJWT]

    def get(self, request):
        from packages.autenticacion_seguridad.services.permisos_operativos_service import (
            PermisosOperativosService,
        )

        return Response({"items": PermisosOperativosService().list_permisos()})


@method_decorator(csrf_exempt, name="dispatch")
class RolPermisosView(APIView):
    """GET/PUT permisos asignados a un rol (app_rol_permisos)."""

    permission_classes = [IsAdminJWT]

    def get(self, request, fk_rol: int):
        from packages.autenticacion_seguridad.services.permisos_operativos_service import (
            PermisosOperativosService,
        )

        return Response({"fk_rol": fk_rol, "permisos": PermisosOperativosService().list_rol_permisos(fk_rol)})

    def put(self, request, fk_rol: int):
        from packages.autenticacion_seguridad.services.permisos_operativos_service import (
            PermisosOperativosService,
        )

        codigos = request.data.get("permisos", [])
        if not isinstance(codigos, list):
            return Response({"error": "permisos debe ser una lista"}, status=400)
        try:
            assigned = PermisosOperativosService().set_rol_permisos(fk_rol, codigos)
            return Response({"fk_rol": fk_rol, "permisos": assigned})
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class BitacoraAccesoListView(APIView):
    """GET — bitácora de accesos (login/logout/intentos fallidos)."""

    permission_classes = [IsAdminJWT]

    def get(self, request):
        from packages.autenticacion_seguridad.services.bitacora_acceso_service import (
            BitacoraAccesoService,
        )

        email = request.query_params.get("email")
        fk = request.query_params.get("fk_usuario")
        tipo = request.query_params.get("tipo_evento")
        limit = int(request.query_params.get("limit", 100))
        return Response(
            {
                "items": BitacoraAccesoService().list_events(
                    email=email,
                    fk_usuario=int(fk) if fk else None,
                    tipo_evento=tipo,
                    limit=limit,
                )
            }
        )
