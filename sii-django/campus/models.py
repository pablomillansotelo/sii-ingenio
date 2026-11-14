from django.db import models
from django.utils import timezone


class AvisoInstitucional(models.Model):
    TIPO_IMPORTANTE = "importante"
    TIPO_INFORMATIVO = "informativo"
    TIPO_CHOICES = [
        (TIPO_IMPORTANTE, "Importante"),
        (TIPO_INFORMATIVO, "Informativo"),
    ]

    titulo = models.CharField(max_length=200)
    cuerpo = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_INFORMATIVO)
    publicado = models.BooleanField(default=False)
    vigencia_inicio = models.DateField(blank=True, null=True)
    vigencia_fin = models.DateField(blank=True, null=True)
    periodo = models.ForeignKey(
        "sii.Periodo",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="avisos_institucionales",
        help_text="Vacío = todos los alumnos.",
    )
    autor_id = models.PositiveIntegerField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_aviso_institucional"
        ordering = ["-creado_en"]

    def __str__(self):
        return self.titulo

    def vigente(self, hoy=None):
        hoy = hoy or timezone.localdate()
        if not self.publicado:
            return False
        if self.vigencia_inicio and hoy < self.vigencia_inicio:
            return False
        if self.vigencia_fin and hoy > self.vigencia_fin:
            return False
        return True


class AvisoLectura(models.Model):
    aviso = models.ForeignKey(AvisoInstitucional, on_delete=models.CASCADE, related_name="lecturas")
    alumno = models.ForeignKey("sii.Alumno", on_delete=models.CASCADE, related_name="lecturas_aviso")
    leido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_aviso_lectura"
        unique_together = ("aviso", "alumno")

    def __str__(self):
        return f"{self.alumno} leyó {self.aviso}"
