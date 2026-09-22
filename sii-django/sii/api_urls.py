from django.urls import include, path
from rest_framework.routers import DefaultRouter

from sii.api_views import AlumnoViewSet, CursoViewSet, InscripcionViewSet, PeriodoViewSet

router = DefaultRouter()
router.register(r"alumnos", AlumnoViewSet, basename="alumno")
router.register(r"cursos", CursoViewSet, basename="curso")
router.register(r"periodos", PeriodoViewSet, basename="periodo")
router.register(r"inscripciones", InscripcionViewSet, basename="inscripcion")

urlpatterns = [
    path("", include(router.urls)),
]
