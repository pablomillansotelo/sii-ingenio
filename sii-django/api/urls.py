"""api URL Configuration — plataforma Ingenio consolidada."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

from . import views
from .views import CustomLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", CustomLoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path(
        "cuenta/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            success_url="/cuenta/recuperar/enviado/",
        ),
        name="password_reset",
    ),
    path(
        "cuenta/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "cuenta/recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url="/cuenta/recuperar/listo/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "cuenta/recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("inicio/", views.inicio, name="inicio"),
    path("sii/", include("sii.urls")),
    path("dashboard/", RedirectView.as_view(pattern_name="sii_home", permanent=False)),
    path(
        "dashboard/<path:rest>/",
        RedirectView.as_view(url="/sii/%(rest)s/", permanent=False),
    ),
    path("alumnos/", include("alumnos.urls")),
    path("", include("alumnos.api_urls")),
    path("docente/", include("docente.urls")),
    path("administrador/", include("administrador.urls")),
    path("cuenta/", include("usuario.urls")),
    path("usuario/", RedirectView.as_view(url="/cuenta/", permanent=False)),
    path("ventas/", include("ventas.urls")),
    path("aula/", include("aula.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)
