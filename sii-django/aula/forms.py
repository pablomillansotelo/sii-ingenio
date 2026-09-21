from django import forms
from django.forms.widgets import CheckboxInput, Select, SelectMultiple, FileInput

from aula.models import Actividad, CalificacionActividad
from docente.models import Docente


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


class ActividadForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ("nombre", "descripcion", "fecha_limite", "valor", "tipo", "estado")
        labels = {
            "nombre": "Nombre",
            "descripcion": "Descripción",
            "fecha_limite": "Fecha límite",
            "valor": "Ponderación",
            "tipo": "Tipo",
            "estado": "Estado",
        }
        widgets = {
            "fecha_limite": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }


class EntregaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CalificacionActividad
        fields = ("entrega",)
        labels = {"entrega": "Tu entrega"}
        widgets = {"entrega": forms.Textarea(attrs={"rows": 5, "placeholder": "Escribe o pega tu entrega."})}


class CalificacionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CalificacionActividad
        fields = ("calificacion", "comentarios")
        labels = {
            "calificacion": "Calificación",
            "comentarios": "Retroalimentación",
        }
        widgets = {
            "comentarios": forms.Textarea(attrs={"rows": 2}),
        }


class AsignarDocenteForm(BootstrapFormMixin, forms.Form):
    docente = forms.ModelChoiceField(queryset=Docente.objects.none(), label="Docente")
    es_coordinador = forms.BooleanField(required=False, label="Coordinador")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["docente"].queryset = Docente.objects.filter(estado="activo").order_by(
            "apellido", "nombre"
        )
