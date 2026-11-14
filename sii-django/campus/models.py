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


class CampusFavorito(models.Model):
    user_id = models.PositiveIntegerField()
    clave = models.CharField(max_length=40)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_favorito"
        unique_together = ("user_id", "clave")

    def __str__(self):
        return f"{self.user_id}:{self.clave}"


class CampusPreferencia(models.Model):
    TEMA_CLARO = "claro"
    TEMA_OSCURO = "oscuro"
    TEMA_CHOICES = [
        (TEMA_CLARO, "Claro"),
        (TEMA_OSCURO, "Oscuro"),
    ]
    ACENTO_ROJO = "rojo"
    ACENTO_VINO = "vino"
    ACENTO_CARBON = "carbon"
    ACENTO_ARENA = "arena"
    ACENTO_CHOICES = [
        (ACENTO_ROJO, "Rojo Ingenio"),
        (ACENTO_VINO, "Vino"),
        (ACENTO_CARBON, "Carbón"),
        (ACENTO_ARENA, "Arena"),
    ]
    ACENTO_HEX = {
        ACENTO_ROJO: "#ce0e2d",
        ACENTO_VINO: "#8a1538",
        ACENTO_CARBON: "#1d2939",
        ACENTO_ARENA: "#9a3412",
    }

    user_id = models.PositiveIntegerField(unique=True)
    tema = models.CharField(max_length=12, choices=TEMA_CHOICES, default=TEMA_CLARO)
    acento = models.CharField(max_length=12, choices=ACENTO_CHOICES, default=ACENTO_ROJO)
    animacion_carga = models.BooleanField(default=True)
    ayuda_guiada = models.BooleanField(default=False)
    asistente_ia = models.BooleanField(default=False)

    class Meta:
        db_table = "campus_preferencia"

    def __str__(self):
        return f"prefs {self.user_id}"

    @property
    def acento_hex(self):
        return self.ACENTO_HEX.get(self.acento, self.ACENTO_HEX[self.ACENTO_ROJO])


class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    cuerpo = models.TextField()
    extracto = models.CharField(max_length=280, blank=True, default="")
    publicada = models.BooleanField(default=False)
    vigencia_inicio = models.DateField(blank=True, null=True)
    vigencia_fin = models.DateField(blank=True, null=True)
    autor_id = models.PositiveIntegerField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_noticia"
        ordering = ["-creada_en"]

    def __str__(self):
        return self.titulo

    def recorte(self):
        if self.extracto:
            return self.extracto
        texto = (self.cuerpo or "").strip()
        return texto[:160] + ("…" if len(texto) > 160 else "")


class Hilo(models.Model):
    asunto = models.CharField(max_length=160)
    para_control = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    creado_por_id = models.PositiveIntegerField()

    class Meta:
        db_table = "campus_hilo"
        ordering = ["-creado_en"]

    def __str__(self):
        return self.asunto


class HiloParticipante(models.Model):
    hilo = models.ForeignKey(Hilo, on_delete=models.CASCADE, related_name="participantes")
    user_id = models.PositiveIntegerField()

    class Meta:
        db_table = "campus_hilo_participante"
        unique_together = ("hilo", "user_id")


class MensajeCampus(models.Model):
    hilo = models.ForeignKey(Hilo, on_delete=models.CASCADE, related_name="mensajes")
    autor_id = models.PositiveIntegerField()
    cuerpo = models.TextField()
    archivo = models.FileField(upload_to="mensajes/%Y/%m/", blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_mensaje"
        ordering = ["creado_en"]


class MensajeLectura(models.Model):
    mensaje = models.ForeignKey(MensajeCampus, on_delete=models.CASCADE, related_name="lecturas")
    user_id = models.PositiveIntegerField()
    leido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_mensaje_lectura"
        unique_together = ("mensaje", "user_id")


class Notificacion(models.Model):
    TIPO_ACTIVIDAD = "actividad"
    TIPO_CALIFICACION = "calificacion"
    TIPO_AVISO = "aviso"
    TIPO_DEUDA = "deuda"
    TIPO_CHOICES = [
        (TIPO_ACTIVIDAD, "Actividad"),
        (TIPO_CALIFICACION, "Calificación"),
        (TIPO_AVISO, "Aviso"),
        (TIPO_DEUDA, "Saldo pendiente"),
    ]

    user_id = models.PositiveIntegerField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    clave = models.CharField(max_length=80)
    titulo = models.CharField(max_length=200)
    cuerpo = models.CharField(max_length=280, blank=True, default="")
    url = models.CharField(max_length=200, blank=True, default="")
    creada_en = models.DateTimeField(auto_now_add=True)
    leida_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "campus_notificacion"
        unique_together = ("user_id", "tipo", "clave")
        ordering = ["-creada_en"]

    def __str__(self):
        return self.titulo
