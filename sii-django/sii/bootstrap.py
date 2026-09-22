"""Estilos Bootstrap compartidos por los formularios de todos los dominios."""
from django.forms.widgets import CheckboxInput, FileInput, Select, SelectMultiple


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
