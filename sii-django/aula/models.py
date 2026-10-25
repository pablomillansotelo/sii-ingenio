from django.db import models
from django.utils import timezone

from sii.models import Curso, Inscripcion


class SeccionTema(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="secciones")
    edicion = models.ForeignKey(
        "ventas.EdicionCurso",
        on_delete=models.CASCADE,
        related_name="secciones_aula",
        blank=True,
        null=True,
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default="")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Sección"
        verbose_name_plural = "Secciones"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.titulo


class Recurso(models.Model):
    TIPO_ARCHIVO = "archivo"
    TIPO_URL = "url"
    TIPO_TEXTO = "texto"
    TIPO_CHOICES = [
        (TIPO_ARCHIVO, "Archivo / PDF"),
        (TIPO_URL, "Liga"),
        (TIPO_TEXTO, "Texto o HTML corto"),
    ]

    seccion = models.ForeignKey(SeccionTema, on_delete=models.CASCADE, related_name="recursos")
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_TEXTO)
    url = models.URLField(blank=True, default="")
    cuerpo = models.TextField(blank=True, default="")
    archivo = models.FileField(upload_to="materiales/%Y/%m/", blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.titulo


class AvisoGrupo(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="avisos_aula")
    edicion = models.ForeignKey(
        "ventas.EdicionCurso",
        on_delete=models.CASCADE,
        related_name="avisos_aula",
        blank=True,
        null=True,
    )
    titulo = models.CharField(max_length=200)
    cuerpo = models.TextField()
    fecha = models.DateTimeField(auto_now=True)
    publicado = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Aviso del grupo"
        verbose_name_plural = "Avisos del grupo"
        ordering = ["-fecha"]

    def __str__(self):
        return self.titulo


class Actividad(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="actividades")
    edicion = models.ForeignKey(
        "ventas.EdicionCurso",
        on_delete=models.SET_NULL,
        related_name="actividades_aula",
        blank=True,
        null=True,
    )
    seccion = models.ForeignKey(
        SeccionTema,
        on_delete=models.SET_NULL,
        related_name="actividades",
        blank=True,
        null=True,
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_asignacion = models.DateField(auto_now_add=True)
    fecha_limite = models.DateField()
    valor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        help_text="Valor máximo de la actividad (ej: 100 puntos)",
    )
    tipo = models.CharField(
        max_length=20,
        choices=[
            ("tarea", "Tarea"),
            ("examen", "Examen"),
            ("proyecto", "Proyecto"),
            ("participacion", "Participación"),
        ],
        default="tarea",
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ("activa", "Activa"),
            ("cerrada", "Cerrada"),
        ],
        default="activa",
    )

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ["-fecha_limite"]

    def __str__(self):
        return f"{self.nombre} - {self.curso}"

    def motivo_cierre_entrega(self, hoy=None):
        hoy = hoy or timezone.localdate()
        if self.estado == "cerrada":
            return "La actividad está cerrada. Ya no se aceptan entregas."
        if self.fecha_limite and hoy > self.fecha_limite:
            return "La fecha límite ya pasó. Ya no se aceptan entregas."
        return ""

    def acepta_entregas(self, hoy=None):
        return not self.motivo_cierre_entrega(hoy)


class CalificacionActividad(models.Model):
    actividad = models.ForeignKey(
        Actividad, on_delete=models.CASCADE, related_name="calificaciones"
    )
    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name="calificaciones_actividades",
    )
    calificacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Calificación obtenida",
    )
    fecha_calificacion = models.DateField(auto_now_add=True)
    comentarios = models.TextField(blank=True, null=True)
    entregado = models.BooleanField(default=False)
    fecha_entrega = models.DateField(blank=True, null=True)
    entrega = models.TextField(blank=True, default="")
    archivo = models.FileField(upload_to="entregas/%Y/%m/", blank=True, null=True)

    class Meta:
        unique_together = ("actividad", "inscripcion")
        verbose_name = "Calificación de Actividad"
        verbose_name_plural = "Calificaciones de Actividades"

    def __str__(self):
        return (
            f"{self.actividad.nombre} - {self.inscripcion.alumno}: "
            f"{self.calificacion or 'Sin calificar'}"
        )


class Kardex(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion, on_delete=models.CASCADE, related_name="kardex"
    )
    calificacion_final = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    fecha_actualizacion = models.DateField(auto_now=True)

    class Meta:
        verbose_name = "Kardex"
        verbose_name_plural = "Kardex"

    def __str__(self):
        return f"Kardex de {self.inscripcion.alumno} para {self.inscripcion.curso}"

    def calcular_promedio(self):
        calificaciones = self.inscripcion.calificaciones_actividades.filter(
            calificacion__isnull=False
        )
        if not calificaciones.exists():
            return None
        total = sum(calif.calificacion for calif in calificaciones)
        return total / calificaciones.count()
