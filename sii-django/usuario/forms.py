from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.forms.widgets import CheckboxInput, Select, SelectMultiple, FileInput


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


class PerfilForm(BootstrapFormMixin, forms.Form):
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, required=False, label="Apellidos")
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono")


class PasswordChangeForm(BootstrapFormMixin, DjangoPasswordChangeForm):
    pass
