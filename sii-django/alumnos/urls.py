from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("home/", RedirectView.as_view(pattern_name="sii_home", permanent=False), name="alumnos_home"),
    path("kardex/", RedirectView.as_view(pattern_name="sii_kardex", permanent=False), name="kardex"),
    path("alumnos/", RedirectView.as_view(pattern_name="sii_alumnos", permanent=False), name="alumnos"),
    path("horario/", RedirectView.as_view(pattern_name="sii_horario", permanent=False), name="horario"),
    path("pagos/", RedirectView.as_view(pattern_name="Pagos", permanent=False), name="pagos"),
]
