from django.db import models


# Create your models here.
class Alumno(models.Model):
    user_id = models.PositiveIntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    curp = models.CharField(max_length=18, unique=True)
    email = models.EmailField(unique=True)
    fecha_nacimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=[
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('graduado', 'Graduado'),
        ('cancelado', 'Cancelado')
    ], default='activo')

    class Meta:
        managed = True
        db_table = 'cat_alumno'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def get_user(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.using('auth').get(pk=self.user_id)

class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'cat_curso'

    def __str__(self):
        return self.nombre
    
class Periodo(models.Model):
    nombre = models.CharField(max_length=50)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        managed = True
        db_table = 'cat_periodo'

    def __str__(self):
        return self.nombre
    

    
class Inscripcion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    intento = models.IntegerField(default=1)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado')
    ], default='activo')

    class Meta:
        unique_together = ('alumno', 'curso')
        managed = True
        db_table = 'tra_inscripcion'

    def __str__(self):
        return f"{self.alumno} inscrito en {self.curso}"
