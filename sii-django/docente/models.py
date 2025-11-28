from django.db import models
from sii.models import Curso


class Docente(models.Model):
    """
    Modelo para docentes del sistema.
    """
    user_id = models.PositiveIntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('licencia', 'En Licencia'),
    ], default='activo')
    fecha_ingreso = models.DateField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'cat_docente'
        verbose_name = 'Docente'
        verbose_name_plural = 'Docentes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def get_user(self):
        """Obtiene el usuario asociado desde la BD de auth"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.using('auth').get(pk=self.user_id)
        except User.DoesNotExist:
            return None


class DocenteCurso(models.Model):
    """
    Relación muchos a muchos entre Docente y Curso.
    Permite asignar docentes a cursos.
    """
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='cursos_asignados')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='docentes_asignados')
    fecha_asignacion = models.DateField(auto_now_add=True)
    es_coordinador = models.BooleanField(default=False)  # Si es el coordinador del curso

    class Meta:
        managed = True
        db_table = 'tra_docente_curso'
        unique_together = ('docente', 'curso')
        verbose_name = 'Asignación Docente-Curso'
        verbose_name_plural = 'Asignaciones Docente-Curso'

    def __str__(self):
        return f"{self.docente} - {self.curso}"
