from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="sii_home"),
    path("alumnos/", views.alumnos_list, name="sii_alumnos"),
    path("alumnos/crear/", views.alumno_crear, name="sii_alumno_crear"),
    path("alumnos/editar/", views.alumno_editar, name="sii_alumno_editar"),
    path("cursos/", views.cursos_list, name="sii_cursos"),
    path("cursos/crear/", views.curso_crear, name="sii_curso_crear"),
    path("cursos/editar/", views.curso_editar, name="sii_curso_editar"),
    path("inscripciones/", views.inscripciones_list, name="sii_inscripciones"),
    path("inscripciones/crear/", views.inscripcion_crear, name="sii_inscripcion_crear"),
    path("inscripciones/baja/", views.inscripcion_baja, name="sii_inscripcion_baja"),
    path("inscripciones/reintento/", views.inscripcion_reintento, name="sii_inscripcion_reintento"),
    path("periodos/", views.periodos_list, name="sii_periodos"),
    path("periodos/crear/", views.periodo_crear, name="sii_periodo_crear"),
    path("periodos/editar/", views.periodo_editar, name="sii_periodo_editar"),
    path("docentes/", views.docentes_list, name="sii_docentes"),
    path("docentes/crear/", views.docente_crear, name="sii_docente_crear"),
    path("docentes/editar/", views.docente_editar, name="sii_docente_editar"),
    path("docentes/asignar/", views.asignacion_crear, name="sii_asignacion_crear"),
    path("docentes/asignacion/quitar/", views.asignacion_quitar, name="sii_asignacion_quitar"),
]
