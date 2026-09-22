from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import EsAdministradorAPI
from sii.serializers import (
    AlumnoSerializer,
    CursoSerializer,
    InscripcionSerializer,
    PeriodoSerializer,
)


class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [EsAdministradorAPI]

    def create(self, request, *args, **kwargs):
        email = request.data.get("email")
        if email and Alumno.objects.filter(email=email).exists():
            alumno = Alumno.objects.get(email=email)
            serializer = self.get_serializer(alumno)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def buscar_por_email(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "Email requerido"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            alumno = Alumno.objects.get(email=email)
        except Alumno.DoesNotExist:
            return Response({"error": "Alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(alumno).data)


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [EsAdministradorAPI]


class PeriodoViewSet(viewsets.ModelViewSet):
    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer
    permission_classes = [EsAdministradorAPI]


class InscripcionViewSet(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.select_related("alumno", "curso", "periodo")
    serializer_class = InscripcionSerializer
    permission_classes = [EsAdministradorAPI]

    def get_queryset(self):
        queryset = super().get_queryset()
        alumno_id = self.request.query_params.get("alumno_id")
        curso_id = self.request.query_params.get("curso_id")
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)
        return queryset
