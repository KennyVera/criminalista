from django.urls import path

from packages.autenticacion_seguridad.views import (
    ActiveSessionsListView,
    CloseActiveSessionView,
    SessionStatusView,
    LoginView,
    LogoutView,
    MeView,
    MfaResendView,
    MfaVerifyView,
    RequestPasswordResetView,
    ResetPasswordView,
    RolesListView,
    SeedAuthView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("mfa/verificar/", MfaVerifyView.as_view(), name="auth-mfa-verify"),
    path("mfa/reenviar/", MfaResendView.as_view(), name="auth-mfa-resend"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("roles/", RolesListView.as_view(), name="auth-roles"),
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
