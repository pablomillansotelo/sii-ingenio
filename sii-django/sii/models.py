from decimal import Decimal

from django.db import models

CALIFICACION_MINIMA = Decimal("6.00")


class Alumno(models.Model):
    user_id = models.PositiveIntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    curp = models.CharField(max_length=18, unique=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
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
    cerrado = models.BooleanField(default=False)

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


class ActaFinal(models.Model):
    ESTADO_BORRADOR = "borrador"
    ESTADO_PUBLICADA = "publicada"
    ESTADO_CERRADA = "cerrada"
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_PUBLICADA, "Publicada"),
        (ESTADO_CERRADA, "Cerrada"),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="actas")
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="actas")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_BORRADOR)
    publicada_por_id = models.PositiveIntegerField(null=True, blank=True)
    publicada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("curso", "periodo")
        managed = True
        db_table = "tra_acta_final"

    def __str__(self):
        return f"Acta {self.curso} · {self.periodo}"

    @property
    def congelada(self):
        return self.estado in (self.ESTADO_PUBLICADA, self.ESTADO_CERRADA) or self.periodo.cerrado


class ActaRenglon(models.Model):
    acta = models.ForeignKey(ActaFinal, on_delete=models.CASCADE, related_name="renglones")
    inscripcion = models.OneToOneField(
        Inscripcion, on_delete=models.CASCADE, related_name="renglon_acta"
    )
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    acreditado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = "tra_acta_renglon"

    def __str__(self):
        return f"{self.inscripcion.alumno} · {self.calificacion}"

    def aplicar_minima(self):
        if self.calificacion is None:
            self.acreditado = False
        else:
            self.acreditado = self.calificacion >= CALIFICACION_MINIMA
        return self.acreditado


class HorarioSlot(models.Model):
    DIAS = [
        (1, "Lunes"),
        (2, "Martes"),
        (3, "Miércoles"),
        (4, "Jueves"),
        (5, "Viernes"),
        (6, "Sábado"),
        (7, "Domingo"),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="horarios")
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="horarios")
    dia = models.PositiveSmallIntegerField(choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    lugar = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        managed = True
        db_table = "cat_horario_slot"
        ordering = ["periodo", "curso", "dia", "hora_inicio"]

    def __str__(self):
        return f"{self.get_dia_display()} {self.hora_inicio:%H:%M} · {self.curso}"


class Docente(models.Model):
    user_id = models.PositiveIntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ("activo", "Activo"),
            ("inactivo", "Inactivo"),
            ("licencia", "En Licencia"),
        ],
        default="activo",
    )
    fecha_ingreso = models.DateField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "cat_docente"
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def get_user(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.using("auth").get(pk=self.user_id)
        except User.DoesNotExist:
            return None


class DocenteCurso(models.Model):
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name="cursos_asignados")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="docentes_asignados")
    fecha_asignacion = models.DateField(auto_now_add=True)
    es_coordinador = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = "tra_docente_curso"
        unique_together = ("docente", "curso")
        verbose_name = "Asignación Docente-Curso"
        verbose_name_plural = "Asignaciones Docente-Curso"

    def __str__(self):
        return f"{self.docente} - {self.curso}"
