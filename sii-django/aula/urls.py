from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="aula_dashboard"),
    path("kardex/", views.kardex, name="aula_kardex"),
    path("cursos/<int:curso_id>/", views.curso_detail, name="aula_curso"),
    path("cursos/<int:curso_id>/actividades/nueva/", views.actividad_nueva, name="aula_actividad_nueva"),
    path("cursos/<int:curso_id>/asignar/", views.asignar_docente, name="aula_asignar_docente"),
    path("actividades/<int:pk>/editar/", views.actividad_editar, name="aula_actividad_editar"),
    path("actividades/<int:pk>/entregar/", views.actividad_entregar, name="aula_entregar"),
    path("actividades/<int:pk>/calificar/", views.actividad_calificar, name="aula_calificar"),
    path(
        "actividades/<int:pk>/calificar/<int:inscripcion_id>/",
        views.actividad_guardar_calificacion,
        name="aula_guardar_calificacion",
    ),
]
