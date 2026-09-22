from django import forms

from aula.models import Actividad, CalificacionActividad
from sii.bootstrap import BootstrapFormMixin


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
        fields = ("entrega", "archivo")
        labels = {"entrega": "Tu entrega", "archivo": "Archivo (opcional)"}
        widgets = {
            "entrega": forms.Textarea(attrs={"rows": 5, "placeholder": "Escribe o pega tu entrega."})
        }


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
