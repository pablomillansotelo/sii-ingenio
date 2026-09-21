from decimal import Decimal

from django.db import models


class Vendedor(models.Model):
    id_vendedor = models.AutoField(primary_key=True)
    user_id = models.PositiveIntegerField()
    nombre = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    activo = models.BooleanField(default=True)
    comision_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        managed = True
        db_table = "cat_vendedor"

    def __str__(self):
        return self.nombre

    @classmethod
    def obtener_o_crear_desde_usuario(cls, user):
        nombre = (user.get_full_name() or "").strip() or user.get_username()
        vendedor, _ = cls.objects.get_or_create(
            user_id=user.pk,
            defaults={"nombre": nombre, "email": user.email or ""},
        )
        return vendedor


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    apellidos = models.CharField(max_length=50)
    direccion = models.CharField(max_length=120)
    email = models.EmailField()
    telefono = models.CharField(max_length=15, blank=True, null=True)
    curp = models.CharField(max_length=18, blank=True, null=True)
    empresa = models.CharField(max_length=100, blank=True, null=True)
    id_alumno_sii = models.ForeignKey(
        "sii.Alumno",
        models.SET_NULL,
        db_column="id_alumno_sii",
        blank=True,
        null=True,
        related_name="clientes_venta",
    )
    notas = models.TextField(blank=True, default="")
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "cat_cliente"

    def __str__(self):
        return f"{self.id_cliente} - {self.nombre} {self.apellidos}"


class Producto(models.Model):
    MODALIDAD_CHOICES = [
        ("online", "En línea"),
        ("presencial", "Presencial"),
        ("hibrido", "Híbrido"),
    ]

    id_producto = models.AutoField(primary_key=True)
    producto = models.CharField(max_length=120)
    precio_unitario = models.DecimalField(max_digits=19, decimal_places=4)
    codigo = models.CharField(max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, default="")
    duracion_horas = models.SmallIntegerField(blank=True, null=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default="online")
    activo = models.BooleanField(default=True)
    id_curso = models.OneToOneField(
        "sii.Curso",
        models.SET_NULL,
        db_column="id_curso_sii",
        blank=True,
        null=True,
        related_name="oferta",
    )

    class Meta:
        managed = True
        db_table = "cat_producto"

    def __str__(self):
        return f"{self.id_producto} - {self.producto}"


class EdicionCurso(models.Model):
    ESTADO_PROGRAMADA = "programada"
    ESTADO_EN_CURSO = "en_curso"
    ESTADO_CERRADA = "cerrada"
    ESTADO_CHOICES = [
        (ESTADO_PROGRAMADA, "Programada"),
        (ESTADO_EN_CURSO, "En curso"),
        (ESTADO_CERRADA, "Cerrada"),
    ]
    ESTADOS_ABIERTOS = (ESTADO_PROGRAMADA, ESTADO_EN_CURSO)

    id_edicion = models.AutoField(primary_key=True)
    id_curso = models.ForeignKey(
        Producto, models.DO_NOTHING, db_column="id_curso", related_name="ediciones"
    )
    codigo_edicion = models.CharField(max_length=30)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    cupo_maximo = models.SmallIntegerField(default=20)
    cupo_ocupado = models.SmallIntegerField(default=0)
    precio_edicion = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PROGRAMADA)
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "cat_edicion_curso"

    def __str__(self):
        return self.codigo_edicion

    @property
    def cupo_disponible(self):
        return max(0, int(self.cupo_maximo or 0) - int(self.cupo_ocupado or 0))

    @property
    def precio_aplicable(self):
        if self.precio_edicion is not None:
            return self.precio_edicion
        return self.id_curso.precio_unitario

    def reservar_cupo(self, plazas=1):
        plazas = int(plazas)
        if plazas <= 0:
            raise ValueError("La cantidad de plazas debe ser mayor a cero")
        if self.cupo_disponible < plazas:
            raise ValueError("Cupo insuficiente en la edición")
        self.cupo_ocupado = int(self.cupo_ocupado or 0) + plazas
        self.save(update_fields=["cupo_ocupado"])

    def liberar_cupo(self, plazas=1):
        plazas = int(plazas)
        self.cupo_ocupado = max(0, int(self.cupo_ocupado or 0) - max(0, plazas))
        self.save(update_fields=["cupo_ocupado"])


class Venta(models.Model):
    ESTADO_CONFIRMADA = "confirmada"
    ESTADO_CANCELADA = "cancelada"
    ESTADO_BORRADOR = "borrador"
    ESTADO_CHOICES = [
        (ESTADO_CONFIRMADA, "Confirmada"),
        (ESTADO_CANCELADA, "Cancelada"),
        (ESTADO_BORRADOR, "Borrador"),
    ]
    PAGO_PENDIENTE = "pendiente"
    PAGO_PARCIAL = "parcial"
    PAGO_PAGADO = "pagado"
    PAGO_CHOICES = [
        (PAGO_PENDIENTE, "Pendiente"),
        (PAGO_PARCIAL, "Parcial"),
        (PAGO_PAGADO, "Pagado"),
    ]

    id_venta = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Cliente, models.DO_NOTHING, db_column="id_cliente")
    fecha = models.DateField(blank=True, null=True)
    id_vendedor = models.ForeignKey(
        Vendedor,
        models.DO_NOTHING,
        db_column="id_vendedor",
        blank=True,
        null=True,
        related_name="ventas",
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="confirmada")
    observaciones = models.TextField(blank=True, default="")
    registrado_en = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    folio = models.CharField(max_length=20, unique=True, blank=True, null=True)
    estado_pago = models.CharField(
        max_length=20, choices=PAGO_CHOICES, default="pendiente"
    )

    class Meta:
        managed = True
        db_table = "tra_venta"

    def __str__(self):
        return self.folio or str(self.id_venta)

    def save(self, *args, **kwargs):
        if not self.folio and self.pk is None:
            super().save(*args, **kwargs)
            self.folio = f"V-{self.pk:06d}"
            return super().save(update_fields=["folio"])
        return super().save(*args, **kwargs)

    @property
    def cliente(self):
        return self.id_cliente

    @property
    def vendedor_nombre(self):
        return self.id_vendedor.nombre if self.id_vendedor_id else "—"

    @property
    def monto(self):
        return sum(detalle.subtotal() for detalle in self.ventadetalle_set.all())

    def actualizar_estado_pago(self):
        total = self.monto or 0
        pagado = sum(pago.monto for pago in self.pagos.all())
        if pagado <= 0:
            estado = "pendiente"
        elif pagado < total:
            estado = "parcial"
        else:
            estado = "pagado"
        if self.estado_pago != estado:
            self.estado_pago = estado
            self.save(update_fields=["estado_pago"])
        return estado


class VentaDetalle(models.Model):
    id_venta_det = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(Venta, models.DO_NOTHING, db_column="id_venta")
    id_producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column="id_producto")
    cantidad = models.IntegerField()
    descuento = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    precio_unitario = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True
    )
    id_edicion = models.ForeignKey(
        EdicionCurso,
        models.DO_NOTHING,
        db_column="id_edicion",
        blank=True,
        null=True,
        related_name="detalles_venta",
    )

    class Meta:
        managed = True
        db_table = "tra_venta_det"
        unique_together = (("id_venta", "id_producto", "id_edicion"),)

    def subtotal(self):
        precio = self.precio_unitario
        if precio is None:
            precio = self.id_producto.precio_unitario
        descuento = self.descuento or 0
        return (precio * self.cantidad) - descuento

    def __str__(self):
        return f"{self.id_producto.producto} - Cantidad: {self.cantidad}"


class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(Venta, models.CASCADE, db_column="id_venta", related_name="pagos")
    monto = models.DecimalField(max_digits=19, decimal_places=4)
    metodo = models.CharField(max_length=20, default="transferencia")
    referencia = models.CharField(max_length=60, blank=True, default="")
    fecha_pago = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default="aplicado")

    class Meta:
        managed = True
        db_table = "tra_pago"

    def __str__(self):
        return f"Pago {self.id_pago} - {self.monto}"
