from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from packages.autenticacion_seguridad.permissions import IsAdminJWT, IsAuthenticatedJWT
from packages.autenticacion_seguridad.services.auth_service import AuthError, AuthService
from packages.autenticacion_seguridad.services.jwt_tokens import decode_access_token
from packages.autenticacion_seguridad.services.password_recovery import PasswordRecoveryService


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
            return Response(
                {"error": str(exc), "code": getattr(exc, "code", "AUTH_ERROR")},
                status=status.HTTP_401_UNAUTHORIZED,
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
            )
        return Response({"message": "Sesión cerrada"}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class MeView(APIView):
    permission_classes = [IsAuthenticatedJWT]

    def get(self, request):
        return Response({"user": request.crimetrack_user})


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
        try:
            result = AuthService().admin_close_session(
                id_sesion,
                admin_id=int(admin["id_usuario"]),
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
