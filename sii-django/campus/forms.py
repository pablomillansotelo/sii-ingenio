import re

from django import forms

from campus.models import CampusPreferencia
from campus.services.fiscal import REGIMENES
from sii.bootstrap import BootstrapFormMixin
from sii.models import Alumno
from ventas.models import Cliente

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


_RFC = re.compile(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$")


class DatosFiscalesForm(BootstrapFormMixin, forms.ModelForm):
    regimen_fiscal = forms.ChoiceField(choices=[("", "Selecciona")] + list(REGIMENES), required=True)

    class Meta:
        model = Cliente
        fields = ("rfc", "razon_social", "codigo_postal_fiscal", "regimen_fiscal")
        labels = {
            "rfc": "RFC",
            "razon_social": "Razón social o nombre",
            "codigo_postal_fiscal": "Código postal fiscal",
            "regimen_fiscal": "Régimen fiscal",
        }

    def clean_rfc(self):
        valor = (self.cleaned_data.get("rfc") or "").strip().upper()
        if not _RFC.match(valor):
            raise forms.ValidationError("El RFC debe tener 12 o 13 caracteres (formato SAT).")
        return valor

    def clean_codigo_postal_fiscal(self):
        valor = (self.cleaned_data.get("codigo_postal_fiscal") or "").strip()
        if not _CP.match(valor):
            raise forms.ValidationError("El código postal fiscal debe tener 5 dígitos.")
        return valor

    def clean_razon_social(self):
        valor = (self.cleaned_data.get("razon_social") or "").strip()
        if len(valor) < 3:
            raise forms.ValidationError("Indica la razón social.")
        return valor


class AparienciaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CampusPreferencia
        fields = ("tema", "acento", "animacion_carga", "ayuda_guiada", "asistente_ia")
        labels = {
            "tema": "Tema",
            "acento": "Color de acento",
            "animacion_carga": "Mostrar animación de carga",
            "ayuda_guiada": "Ayuda guiada",
            "asistente_ia": "Asistente IA (próximamente)",
        }
        widgets = {
            "tema": forms.RadioSelect,
            "acento": forms.RadioSelect,
        }
