from datetime import date

from django import forms
from django.forms.widgets import CheckboxInput, Select, SelectMultiple, FileInput

from ventas.models import Cliente, Producto, Venta, VentaDetalle, Vendedor, EdicionCurso, Pago


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (Select, SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            elif not isinstance(widget, FileInput):
                existing = widget.attrs.get("class", "")
                if "form-control" not in existing:
                    widget.attrs["class"] = (existing + " form-control").strip()


class AddClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = (
            "nombre",
            "apellidos",
            "direccion",
            "email",
            "telefono",
            "curp",
            "empresa",
            "notas",
            "activo",
        )
        labels = {
            "nombre": "Nombre",
            "apellidos": "Apellidos",
            "direccion": "Dirección",
            "email": "Email",
            "telefono": "Teléfono",
            "curp": "CURP",
            "empresa": "Empresa",
            "notas": "Notas",
            "activo": "Activo",
        }


class EditarClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = (
            "id_cliente",
            "nombre",
            "apellidos",
            "direccion",
            "email",
            "telefono",
            "curp",
            "empresa",
            "notas",
            "activo",
        )
        labels = {
            "id_cliente": "ID",
            "nombre": "Nombre",
            "apellidos": "Apellidos",
            "direccion": "Dirección",
            "email": "Email",
            "telefono": "Teléfono",
            "curp": "CURP",
            "empresa": "Empresa",
            "notas": "Notas",
            "activo": "Activo",
        }
        widgets = {
            "id_cliente": forms.HiddenInput(attrs={"id": "id_cliente_editar"}),
            "nombre": forms.TextInput(attrs={"id": "nombre_editar"}),
            "apellidos": forms.TextInput(attrs={"id": "apellidos_editar"}),
            "direccion": forms.TextInput(attrs={"id": "direccion_editar"}),
            "email": forms.TextInput(attrs={"id": "email_editar"}),
            "telefono": forms.TextInput(attrs={"id": "telefono_editar"}),
            "curp": forms.TextInput(attrs={"id": "curp_editar"}),
            "empresa": forms.TextInput(attrs={"id": "empresa_editar"}),
            "notas": forms.Textarea(attrs={"id": "notas_editar", "rows": 3}),
            "activo": forms.CheckboxInput(attrs={"id": "activo_editar"}),
        }


class AddProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = (
            "producto",
            "precio_unitario",
            "codigo",
            "descripcion",
            "duracion_horas",
            "modalidad",
            "activo",
        )
        labels = {
            "producto": "Curso",
            "precio_unitario": "Precio unitario",
            "codigo": "Código",
            "descripcion": "Descripción",
            "duracion_horas": "Duración (horas)",
            "modalidad": "Modalidad",
            "activo": "Activo",
        }


class EditarProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = (
            "id_producto",
            "producto",
            "precio_unitario",
            "codigo",
            "descripcion",
            "duracion_horas",
            "modalidad",
            "activo",
        )
        labels = {
            "id_producto": "ID",
            "producto": "Curso",
            "precio_unitario": "Precio unitario",
            "codigo": "Código",
            "descripcion": "Descripción",
            "duracion_horas": "Duración (horas)",
            "modalidad": "Modalidad",
            "activo": "Activo",
        }
        widgets = {
            "id_producto": forms.HiddenInput(attrs={"id": "id_producto_editar"}),
            "producto": forms.TextInput(attrs={"id": "producto_editar"}),
            "precio_unitario": forms.NumberInput(attrs={"id": "precio_unitario_editar"}),
            "codigo": forms.TextInput(attrs={"id": "codigo_editar"}),
            "descripcion": forms.Textarea(attrs={"id": "descripcion_editar", "rows": 3}),
            "duracion_horas": forms.NumberInput(attrs={"id": "duracion_horas_editar"}),
            "modalidad": forms.Select(attrs={"id": "modalidad_editar"}),
            "activo": forms.CheckboxInput(attrs={"id": "activo_producto_editar"}),
        }


class EditarVentaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Venta
        fields = ("id_venta", "id_cliente", "fecha", "folio", "estado", "estado_pago", "observaciones")
        labels = {
            "id_venta": "ID",
            "id_cliente": "Cliente",
            "fecha": "Fecha",
            "folio": "Folio",
            "estado": "Estado",
            "estado_pago": "Estado de pago",
            "observaciones": "Observaciones",
        }
        widgets = {
            "id_venta": forms.HiddenInput(attrs={"class": "form-control", "id": "id_venta_editar"}),
            "id_cliente": forms.Select(attrs={"class": "form-control", "id": "id_cliente_editar"}),
            "fecha": forms.DateInput(
                format=("%Y-%m-%d"),
                attrs={"class": "form-control", "type": "date", "id": "fecha_editar"},
            ),
            "folio": forms.TextInput(attrs={"class": "form-control", "id": "folio_editar"}),
            "estado": forms.Select(attrs={"class": "form-control", "id": "estado_editar"}),
            "estado_pago": forms.Select(attrs={"class": "form-control", "id": "estado_pago_editar"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "id": "observaciones_editar", "rows": 3}),
        }


class AddVentaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Venta
        fields = ("id_cliente", "fecha", "observaciones")
        labels = {
            "id_cliente": "Cliente",
            "fecha": "Fecha",
            "observaciones": "Observaciones",
        }
        widgets = {
            "id_cliente": forms.Select(attrs={"class": "form-select", "id": "id_cliente_add"}),
            "fecha": forms.DateInput(
                format=("%Y-%m-%d"),
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "id": "fecha_add",
                    "value": date.today(),
                },
            ),
            "observaciones": forms.Textarea(
                attrs={"class": "form-control", "id": "observaciones_add", "rows": 2}
            ),
        }


class AddVentaDetalleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = VentaDetalle
        fields = ("id_producto", "id_edicion", "cantidad", "descuento")
        labels = {
            "id_producto": "Curso",
            "id_edicion": "Edición",
            "cantidad": "Plazas",
            "descuento": "Descuento",
        }
        widgets = {
            "id_producto": forms.Select(attrs={"class": "form-select", "id": "id_producto_add"}),
            "id_edicion": forms.Select(attrs={"class": "form-select", "id": "id_edicion_add"}),
            "cantidad": forms.NumberInput(
                attrs={"class": "form-control", "id": "cantidad_add", "min": "1", "value": "1"}
            ),
            "descuento": forms.NumberInput(
                attrs={"class": "form-control", "id": "descuento_add", "step": "0.01", "min": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_producto"].queryset = Producto.objects.filter(activo=True).order_by("producto")
        self.fields["id_edicion"].queryset = EdicionCurso.objects.filter(
            activo=True,
            estado__in=EdicionCurso.ESTADOS_ABIERTOS,
        ).select_related("id_curso").order_by("codigo_edicion")
        self.fields["id_edicion"].required = False
        self.fields["id_edicion"].empty_label = "Sin edición"
        self.fields["id_edicion"].label_from_instance = (
            lambda obj: f"{obj.codigo_edicion} · {obj.cupo_disponible} lugares"
        )
        self.fields["cantidad"].initial = 1


class AddVendedorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Vendedor
        fields = ("nombre", "email", "telefono", "comision_pct", "activo")
        labels = {
            "nombre": "Nombre",
            "email": "Email",
            "telefono": "Teléfono",
            "comision_pct": "Comisión %",
            "activo": "Activo",
        }


class EditarVendedorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Vendedor
        fields = ("id_vendedor", "nombre", "email", "telefono", "comision_pct", "activo")
        widgets = {
            "id_vendedor": forms.HiddenInput(attrs={"id": "id_vendedor_editar"}),
            "nombre": forms.TextInput(attrs={"id": "nombre_vendedor_editar"}),
            "email": forms.EmailInput(attrs={"id": "email_vendedor_editar"}),
            "telefono": forms.TextInput(attrs={"id": "telefono_vendedor_editar"}),
            "comision_pct": forms.NumberInput(attrs={"id": "comision_vendedor_editar"}),
            "activo": forms.CheckboxInput(attrs={"id": "activo_vendedor_editar"}),
        }


class AddEdicionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EdicionCurso
        fields = (
            "id_curso",
            "codigo_edicion",
            "fecha_inicio",
            "fecha_fin",
            "cupo_maximo",
            "precio_edicion",
            "estado",
            "activo",
        )
        labels = {
            "id_curso": "Curso",
            "codigo_edicion": "Código de edición",
            "fecha_inicio": "Inicio",
            "fecha_fin": "Fin",
            "cupo_maximo": "Cupo",
            "precio_edicion": "Precio de edición",
            "estado": "Estado",
            "activo": "Activo",
        }
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }


class EditarEdicionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EdicionCurso
        fields = (
            "id_edicion",
            "id_curso",
            "codigo_edicion",
            "fecha_inicio",
            "fecha_fin",
            "cupo_maximo",
            "precio_edicion",
            "estado",
            "activo",
        )
        widgets = {
            "id_edicion": forms.HiddenInput(attrs={"id": "id_edicion_editar"}),
            "id_curso": forms.Select(attrs={"id": "id_curso_edicion_editar"}),
            "codigo_edicion": forms.TextInput(attrs={"id": "codigo_edicion_editar"}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date", "id": "fecha_inicio_edicion_editar"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "id": "fecha_fin_edicion_editar"}),
            "cupo_maximo": forms.NumberInput(attrs={"id": "cupo_edicion_editar"}),
            "precio_edicion": forms.NumberInput(attrs={"id": "precio_edicion_editar"}),
            "estado": forms.Select(attrs={"id": "estado_edicion_editar"}),
            "activo": forms.CheckboxInput(attrs={"id": "activo_edicion_editar"}),
        }


class AddPagoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pago
        fields = ("id_venta", "monto", "metodo", "referencia")
        labels = {
            "id_venta": "Venta",
            "monto": "Monto",
            "metodo": "Método",
            "referencia": "Referencia",
        }


class EditarPagoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pago
        fields = ("id_pago", "id_venta", "monto", "metodo", "referencia", "estado")
        widgets = {
            "id_pago": forms.HiddenInput(attrs={"id": "id_pago_editar"}),
            "id_venta": forms.Select(attrs={"id": "id_venta_pago_editar"}),
            "monto": forms.NumberInput(attrs={"id": "monto_pago_editar"}),
            "metodo": forms.TextInput(attrs={"id": "metodo_pago_editar"}),
            "referencia": forms.TextInput(attrs={"id": "referencia_pago_editar"}),
            "estado": forms.TextInput(attrs={"id": "estado_pago_reg_editar"}),
        }
