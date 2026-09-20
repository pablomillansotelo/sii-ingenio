from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="sii_home"),
    path("alumnos/", views.alumnos_list, name="sii_alumnos"),
    path("cursos/", views.cursos_list, name="sii_cursos"),
    path("inscripciones/", views.inscripciones_list, name="sii_inscripciones"),
    path("periodos/", views.periodos_list, name="sii_periodos"),
    path("docentes/", views.docentes_list, name="sii_docentes"),
]
