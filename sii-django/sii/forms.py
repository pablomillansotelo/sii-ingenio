from django import forms
from django.forms.widgets import CheckboxInput, Select, SelectMultiple, FileInput

from docente.models import Docente, DocenteCurso
from sii.models import Alumno, Curso, Inscripcion, Periodo


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


class AlumnoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ("nombre", "apellido", "email", "curp", "fecha_nacimiento", "estado")
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellidos",
            "email": "Email",
            "curp": "CURP",
            "fecha_nacimiento": "Fecha de nacimiento",
            "estado": "Estado",
        }
        widgets = {"fecha_nacimiento": forms.DateInput(attrs={"type": "date"})}


class EditarAlumnoForm(AlumnoForm):
    class Meta(AlumnoForm.Meta):
        fields = ("id",) + AlumnoForm.Meta.fields
        widgets = {
            **AlumnoForm.Meta.widgets,
            "id": forms.HiddenInput(attrs={"id": "id_alumno_editar"}),
            "nombre": forms.TextInput(attrs={"id": "nombre_alumno_editar"}),
            "apellido": forms.TextInput(attrs={"id": "apellido_alumno_editar"}),
            "email": forms.EmailInput(attrs={"id": "email_alumno_editar"}),
            "curp": forms.TextInput(attrs={"id": "curp_alumno_editar", "maxlength": "18"}),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "id": "nacimiento_alumno_editar"}),
            "estado": forms.Select(attrs={"id": "estado_alumno_editar"}),
        }


class PeriodoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Periodo
        fields = ("nombre", "fecha_inicio", "fecha_fin")
        labels = {
            "nombre": "Periodo",
            "fecha_inicio": "Inicio",
            "fecha_fin": "Fin",
        }
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }


class EditarPeriodoForm(PeriodoForm):
    class Meta(PeriodoForm.Meta):
        fields = ("id",) + PeriodoForm.Meta.fields
        widgets = {
            "id": forms.HiddenInput(attrs={"id": "id_periodo_editar"}),
            "nombre": forms.TextInput(attrs={"id": "nombre_periodo_editar"}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date", "id": "inicio_periodo_editar"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "id": "fin_periodo_editar"}),
        }


class CursoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Curso
        fields = ("nombre", "descripcion")
        labels = {"nombre": "Nombre", "descripcion": "Descripción"}
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}


class EditarCursoForm(CursoForm):
    class Meta(CursoForm.Meta):
        fields = ("id",) + CursoForm.Meta.fields
        widgets = {
            "id": forms.HiddenInput(attrs={"id": "id_curso_editar"}),
            "nombre": forms.TextInput(attrs={"id": "nombre_curso_editar"}),
            "descripcion": forms.Textarea(attrs={"rows": 3, "id": "descripcion_curso_editar"}),
        }


class DocenteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Docente
        fields = ("nombre", "apellido", "email", "telefono", "especialidad", "estado")
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellidos",
            "email": "Email",
            "telefono": "Teléfono",
            "especialidad": "Especialidad",
            "estado": "Estado",
        }


class EditarDocenteForm(DocenteForm):
    class Meta(DocenteForm.Meta):
        fields = ("id",) + DocenteForm.Meta.fields
        widgets = {
            "id": forms.HiddenInput(attrs={"id": "id_docente_editar"}),
            "nombre": forms.TextInput(attrs={"id": "nombre_docente_editar"}),
            "apellido": forms.TextInput(attrs={"id": "apellido_docente_editar"}),
            "email": forms.EmailInput(attrs={"id": "email_docente_editar"}),
            "telefono": forms.TextInput(attrs={"id": "telefono_docente_editar"}),
            "especialidad": forms.TextInput(attrs={"id": "especialidad_docente_editar"}),
            "estado": forms.Select(attrs={"id": "estado_docente_editar"}),
        }


class InscripcionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ("alumno", "curso", "periodo")
        labels = {"alumno": "Alumno", "curso": "Curso", "periodo": "Periodo"}


class AsignacionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DocenteCurso
        fields = ("docente", "curso", "es_coordinador")
        labels = {
            "docente": "Docente",
            "curso": "Curso",
            "es_coordinador": "Coordinador",
        }
