from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from sii.models import Alumno, Curso, Periodo, Inscripcion
from .serializers import AlumnoSerializer, CursoSerializer, PeriodoSerializer, InscripcionSerializer


class AlumnoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar alumnos.
    Permite crear, leer, actualizar y eliminar alumnos.
    """
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo alumno.
        Si el email ya existe, retorna el alumno existente.
        """
        email = request.data.get('email')
        if email and Alumno.objects.filter(email=email).exists():
            alumno = Alumno.objects.get(email=email)
            serializer = self.get_serializer(alumno)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def buscar_por_email(self, request):
        """Busca un alumno por email"""
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            alumno = Alumno.objects.get(email=email)
            serializer = self.get_serializer(alumno)
            return Response(serializer.data)
        except Alumno.DoesNotExist:
            return Response({'error': 'Alumno no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class CursoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar cursos"""
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer


class PeriodoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar períodos"""
    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer


class InscripcionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar inscripciones"""
    queryset = Inscripcion.objects.select_related('alumno', 'curso', 'periodo').all()
    serializer_class = InscripcionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        alumno_id = self.request.query_params.get('alumno_id')
        curso_id = self.request.query_params.get('curso_id')
        
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)
        
        return queryset

