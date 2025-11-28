from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AlumnoViewSet, CursoViewSet, PeriodoViewSet, InscripcionViewSet

router = DefaultRouter()
router.register(r'alumnos', AlumnoViewSet, basename='alumno')
router.register(r'cursos', CursoViewSet, basename='curso')
router.register(r'periodos', PeriodoViewSet, basename='periodo')
router.register(r'inscripciones', InscripcionViewSet, basename='inscripcion')

urlpatterns = [
    path('api/', include(router.urls)),
]

