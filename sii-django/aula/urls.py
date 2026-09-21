from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="aula_dashboard"),
    path("kardex/", RedirectView.as_view(pattern_name="sii_kardex", permanent=False), name="aula_kardex"),
    path("cursos/<int:curso_id>/", views.curso_detail, name="aula_curso"),
    path("cursos/<int:curso_id>/actividades/nueva/", views.actividad_nueva, name="aula_actividad_nueva"),
    path("cursos/<int:curso_id>/asignar/", RedirectView.as_view(url="/sii/docentes/", query_string=False, permanent=False), name="aula_asignar_docente"),
    path("actividades/<int:pk>/editar/", views.actividad_editar, name="aula_actividad_editar"),
    path("actividades/<int:pk>/entregar/", views.actividad_entregar, name="aula_entregar"),
    path("actividades/<int:pk>/calificar/", views.actividad_calificar, name="aula_calificar"),
    path(
        "actividades/<int:pk>/calificar/<int:inscripcion_id>/",
        views.actividad_guardar_calificacion,
        name="aula_guardar_calificacion",
    ),
    path(
        "actividades/<int:pk>/calificar/todas/",
        views.actividad_guardar_calificaciones,
        name="aula_guardar_calificaciones",
    ),
    path("por-calificar/", views.por_calificar, name="aula_por_calificar"),
]
