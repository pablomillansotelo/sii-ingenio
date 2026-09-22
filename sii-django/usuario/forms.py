from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm

from sii.bootstrap import BootstrapFormMixin


class PerfilForm(BootstrapFormMixin, forms.Form):
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, required=False, label="Apellidos")
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono")


class PasswordChangeForm(BootstrapFormMixin, DjangoPasswordChangeForm):
    pass
