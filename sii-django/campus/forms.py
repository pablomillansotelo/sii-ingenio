import re

from django import forms

from campus.models import CampusPreferencia
from sii.bootstrap import BootstrapFormMixin
from sii.models import Alumno

_TELEFONO = re.compile(r"^\d{10}$")
_CP = re.compile(r"^\d{5}$")


def _limpio_telefono(valor, etiqueta):
    valor = (valor or "").strip()
    if not valor:
        return ""
    digitos = re.sub(r"\D", "", valor)
    if not _TELEFONO.match(digitos):
        raise forms.ValidationError(f"El {etiqueta} debe tener 10 dígitos.")
    return digitos


class FichaAlumnoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Alumno
        fields = (
            "telefono",
            "email_personal",
            "direccion_calle",
            "colonia",
            "codigo_postal",
            "ciudad",
            "estado_domicilio",
            "empresa",
            "puesto",
            "telefono_laboral",
            "contacto_emergencia_nombre",
            "contacto_emergencia_telefono",
        )
        labels = {
            "telefono": "Teléfono personal",
            "email_personal": "Correo personal",
            "direccion_calle": "Calle y número",
            "colonia": "Colonia",
            "codigo_postal": "Código postal",
            "ciudad": "Ciudad",
            "estado_domicilio": "Estado",
            "empresa": "Empresa (opcional)",
            "puesto": "Puesto (opcional)",
            "telefono_laboral": "Teléfono laboral (opcional)",
            "contacto_emergencia_nombre": "Contacto de emergencia",
            "contacto_emergencia_telefono": "Teléfono de emergencia",
        }

    def clean_telefono(self):
        return _limpio_telefono(self.cleaned_data.get("telefono"), "teléfono")

    def clean_telefono_laboral(self):
        return _limpio_telefono(self.cleaned_data.get("telefono_laboral"), "teléfono laboral")

    def clean_contacto_emergencia_telefono(self):
        return _limpio_telefono(
            self.cleaned_data.get("contacto_emergencia_telefono"), "teléfono de emergencia"
        )

    def clean_codigo_postal(self):
        valor = (self.cleaned_data.get("codigo_postal") or "").strip()
        if not valor:
            return ""
        if not _CP.match(valor):
            raise forms.ValidationError("El código postal debe tener 5 dígitos.")
        return valor


class AparienciaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CampusPreferencia
        fields = ("tema", "acento", "animacion_carga")
        labels = {
            "tema": "Tema",
            "acento": "Color de acento",
            "animacion_carga": "Mostrar animación de carga",
        }
        widgets = {
            "tema": forms.RadioSelect,
            "acento": forms.RadioSelect,
        }
