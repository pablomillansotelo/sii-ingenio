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


class PerfilLudico(models.Model):
    alumno = models.OneToOneField("sii.Alumno", on_delete=models.CASCADE, related_name="perfil_ludico")
    xp = models.PositiveIntegerField(default=0)
    monedas = models.PositiveIntegerField(default=0)
    ranking_publico = models.BooleanField(default=False)
    actualizado_en = models.DateTimeField(auto_now=True)
    reset_en = models.DateTimeField(blank=True, null=True)
    reset_por_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "campus_perfil_ludico"

    def __str__(self):
        return f"Ludico {self.alumno_id}"

    @property
    def nivel(self):
        return 1 + int(self.xp) // 100


class Insignia(models.Model):
    clave = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        db_table = "campus_insignia"

    def __str__(self):
        return self.nombre


class InsigniaAlumno(models.Model):
    perfil = models.ForeignKey(PerfilLudico, on_delete=models.CASCADE, related_name="insignias")
    insignia = models.ForeignKey(Insignia, on_delete=models.CASCADE)
    obtenida_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_insignia_alumno"
        unique_together = ("perfil", "insignia")


class MovimientoXP(models.Model):
    perfil = models.ForeignKey(PerfilLudico, on_delete=models.CASCADE, related_name="movimientos")
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=160)
    clave = models.CharField(max_length=80)
    creado_en = models.DateTimeField(auto_now_add=True)
    creado_por_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "campus_movimiento_xp"
        unique_together = ("perfil", "clave")
        ordering = ["-creado_en"]


class RetoSemanal(models.Model):
    alumno = models.ForeignKey("sii.Alumno", on_delete=models.CASCADE, related_name="retos_semanales")
    inscripcion = models.ForeignKey("sii.Inscripcion", on_delete=models.CASCADE, related_name="retos_semanales")
    semana = models.DateField()
    meta = models.PositiveIntegerField(default=1)
    progreso = models.PositiveIntegerField(default=0)
    completado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "campus_reto_semanal"
        unique_together = ("inscripcion", "semana")
        ordering = ["semana", "id"]

    @property
    def porcentaje(self):
        if not self.meta:
            return 0
        return min(100, int(round(100 * self.progreso / self.meta)))


class DocumentoNormativa(models.Model):
    titulo = models.CharField(max_length=200)
    cuerpo = models.TextField(blank=True, default="")
    archivo = models.FileField(upload_to="normativa/%Y/%m/", blank=True, null=True)
    publicado = models.BooleanField(default=False)
    autor_id = models.PositiveIntegerField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_documento_normativa"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo


class ContactoDirectorio(models.Model):
    area = models.CharField(max_length=80)
    nombre = models.CharField(max_length=120)
    medio = models.CharField(max_length=160, help_text="Correo, teléfono o horario.")
    publicado = models.BooleanField(default=False)
    autor_id = models.PositiveIntegerField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_contacto_directorio"
        ordering = ["area", "nombre"]

    def __str__(self):
        return f"{self.area}: {self.nombre}"


class TicketAyuda(models.Model):
    ESTADO_ABIERTO = "abierto"
    ESTADO_ATENCION = "en_atencion"
    ESTADO_RESUELTO = "resuelto"
    ESTADO_CERRADO = "cerrado"
    ESTADO_CHOICES = [
        (ESTADO_ABIERTO, "Abierto"),
        (ESTADO_ATENCION, "En atención"),
        (ESTADO_RESUELTO, "Resuelto"),
        (ESTADO_CERRADO, "Cerrado"),
    ]
    CATEGORIA_CHOICES = [
        ("academico", "Académico"),
        ("administrativo", "Administrativo"),
        ("tecnico", "Técnico"),
        ("otro", "Otro"),
    ]

    alumno = models.ForeignKey("sii.Alumno", on_delete=models.CASCADE, related_name="tickets")
    folio = models.CharField(max_length=20, unique=True, blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    asunto = models.CharField(max_length=160)
    descripcion = models.TextField()
    adjunto = models.FileField(upload_to="ayuda/%Y/%m/", blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ABIERTO)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campus_ticket_ayuda"
        ordering = ["-creado_en"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.folio:
            self.folio = f"AYU-{self.pk:06d}"
            super().save(update_fields=["folio"])

    def __str__(self):
        return self.folio or str(self.pk)


class TicketRespuesta(models.Model):
    ticket = models.ForeignKey(TicketAyuda, on_delete=models.CASCADE, related_name="respuestas")
    autor_id = models.PositiveIntegerField()
    es_staff = models.BooleanField(default=False)
    cuerpo = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campus_ticket_respuesta"
        ordering = ["creado_en"]

