from django.urls import path

from packages.autenticacion_seguridad.views import (
    ActiveSessionsListView,
    BitacoraAccesoListView,
    CloseActiveSessionView,
    LoginView,
    LogoutView,
    MeView,
    MfaResendView,
    MfaVerifyView,
    PermisosListView,
    RequestPasswordResetView,
    ResetPasswordView,
    RolPermisosView,
    RolesListView,
    SeedAuthView,
    SessionStatusView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("mfa/verificar/", MfaVerifyView.as_view(), name="auth-mfa-verify"),
    path("mfa/reenviar/", MfaResendView.as_view(), name="auth-mfa-resend"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("roles/", RolesListView.as_view(), name="auth-roles"),
    path("permisos/", PermisosListView.as_view(), name="auth-permisos"),
    path("roles/<int:fk_rol>/permisos/", RolPermisosView.as_view(), name="auth-rol-permisos"),
    path("bitacora-acceso/", BitacoraAccesoListView.as_view(), name="auth-bitacora-acceso"),
    path("sesiones-activas/", ActiveSessionsListView.as_view(), name="auth-active-sessions"),
    path(
        "sesiones-activas/<int:id_sesion>/cerrar/",
        CloseActiveSessionView.as_view(),
        name="auth-close-session",
    ),
    path("sesion-estado/", SessionStatusView.as_view(), name="auth-session-status"),
    path("recuperar-contrasena/", RequestPasswordResetView.as_view(), name="auth-request-reset"),
    path("restablecer-contrasena/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("seed/", SeedAuthView.as_view(), name="auth-seed"),
]
