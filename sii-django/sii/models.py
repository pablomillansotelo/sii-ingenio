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
    id_edicion = models.ForeignKey(
        "ventas.EdicionCurso",
        models.SET_NULL,
        db_column="id_edicion",
        blank=True,
        null=True,
        related_name="inscripciones_sii",
    )
    intento = models.IntegerField(default=1)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado')
    ], default='activo')
    puede_cursar = models.BooleanField(default=True)

    class Meta:
        unique_together = ('alumno', 'curso', 'periodo')
        managed = True
        db_table = 'tra_inscripcion'

    def __str__(self):
        return f"{self.alumno} inscrito en {self.curso}"

    def dar_baja(self, liberar=True):
        if self.estado == "cancelado":
            raise ValueError("La inscripción ya está dada de baja")
        self.estado = "cancelado"
        self.puede_cursar = False
        self.save(update_fields=["estado", "puede_cursar"])
        if liberar:
            self._liberar_cupo()
        return self

    def reintentar(self, periodo=None, reservar=True):
        if self.estado != "cancelado":
            raise ValueError("Solo se reintenta una inscripción dada de baja")
        self.intento = int(self.intento or 1) + 1
        self.estado = "activo"
        self.calificacion = None
        self.puede_cursar = True
        campos = ["intento", "estado", "calificacion", "puede_cursar"]
        if periodo is not None:
            self.periodo = periodo
            campos.append("periodo")
        self.save(update_fields=campos)
        if reservar:
            self._reservar_cupo()
        return self

    def _edicion(self):
        return self.id_edicion

    def _reservar_cupo(self, plazas=1):
        edicion = self._edicion()
        if edicion is None:
            return
        edicion.reservar_cupo(plazas)

    def _liberar_cupo(self, plazas=1):
        edicion = self._edicion()
        if edicion is None:
            return
        edicion.liberar_cupo(plazas)

    @classmethod
    def de_alumno_en_curso(cls, alumno, curso):
        if alumno is None:
            return None
        return (
            cls.objects.filter(alumno=alumno, curso=curso)
            .select_related("periodo", "id_edicion")
            .order_by("-periodo__fecha_inicio", "-id")
            .first()
        )
