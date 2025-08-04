from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Alumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='alumno')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    curp = models.CharField(max_length=18, unique=True)
    email = models.EmailField(unique=True)
    fecha_nacimiento = models.DateField()

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def __str__(self):
        return self.nombre
    
class Inscripcion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    intento = models.IntegerField(default=1)

    class Meta:
        unique_together = ('alumno', 'curso')

    def __str__(self):
        return f"{self.alumno} inscrito en {self.curso}"

class Kardex(models.Model):
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Kardex de {self.inscripcion.alumno} para {self.inscripcion.curso}"
