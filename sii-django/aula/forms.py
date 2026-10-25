from django import forms

from aula.models import Actividad, AvisoGrupo, CalificacionActividad, Recurso, SeccionTema
from sii.bootstrap import BootstrapFormMixin


class ActividadForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ("nombre", "descripcion", "fecha_limite", "valor", "tipo", "estado", "seccion")
        labels = {
            "nombre": "Nombre",
            "descripcion": "Descripción",
            "fecha_limite": "Fecha límite",
            "valor": "Ponderación",
            "tipo": "Tipo",
            "estado": "Estado",
            "seccion": "Sección / tema",
        }
        widgets = {
            "fecha_limite": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, curso=None, edicion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["seccion"].required = False
        self.fields["seccion"].empty_label = "Sin sección"
        qs = SeccionTema.objects.none()
        if curso is not None:
            qs = SeccionTema.objects.filter(curso=curso)
            if edicion is not None:
                qs = qs.filter(edicion=edicion)
            elif self.instance.pk and self.instance.edicion_id:
                qs = qs.filter(edicion=self.instance.edicion)
        self.fields["seccion"].queryset = qs


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


class SeccionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SeccionTema
        fields = ("titulo", "descripcion", "orden")
        labels = {
            "titulo": "Tema",
            "descripcion": "Descripción",
            "orden": "Orden",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
        }


class RecursoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Recurso
        fields = ("titulo", "tipo", "url", "cuerpo", "archivo", "orden")
        labels = {
            "titulo": "Título",
            "tipo": "Tipo",
            "url": "Liga",
            "cuerpo": "Texto o HTML corto",
            "archivo": "Archivo",
            "orden": "Orden",
        }
        widgets = {
            "cuerpo": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        if tipo == Recurso.TIPO_URL and not cleaned.get("url"):
            self.add_error("url", "Indica la liga del recurso.")
        if tipo == Recurso.TIPO_TEXTO and not (cleaned.get("cuerpo") or "").strip():
            self.add_error("cuerpo", "Escribe el texto o HTML corto.")
        if tipo == Recurso.TIPO_ARCHIVO and not cleaned.get("archivo") and not self.instance.archivo:
            self.add_error("archivo", "Sube un PDF u otro archivo.")
        return cleaned


class AvisoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AvisoGrupo
        fields = ("titulo", "cuerpo", "publicado")
        labels = {
            "titulo": "Título",
            "cuerpo": "Recado",
            "publicado": "Visible para el grupo",
        }
        widgets = {
            "cuerpo": forms.Textarea(attrs={"rows": 4}),
        }
