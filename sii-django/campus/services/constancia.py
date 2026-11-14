"""Constancia de estudios. Fuente SII (alumno + inscripciones), no Ventas."""

from pathlib import Path

from django.conf import settings
from django.utils import timezone
from fpdf import FPDF

from sii.models import Inscripcion

ROJO = (206, 14, 45)
GRIS = (90, 90, 90)
NEGRO = (33, 33, 33)

TIPO_INSCRIPCION = "inscripcion"
TIPO_HISTORIAL = "historial"


def _txt(value, vacio="-"):
    if value is None or value == "":
        return vacio
    texto = str(value)
    for origen, destino in (("—", "-"), ("–", "-"), ("“", '"'), ("”", '"'), ("•", "-")):
        texto = texto.replace(origen, destino)
    return texto.encode("latin-1", "replace").decode("latin-1")


def inscripciones_de(alumno):
    if alumno is None:
        return Inscripcion.objects.none()
    return Inscripcion.objects.filter(alumno=alumno).select_related("curso", "periodo").order_by(
        "-periodo__fecha_inicio", "curso__nombre"
    )


def es_alumno_regular(alumno):
    return inscripciones_de(alumno).filter(estado="activo").exists() and alumno.estado == "activo"


def tipos_disponibles(alumno):
    tipos = [TIPO_HISTORIAL]
    if es_alumno_regular(alumno):
        tipos.insert(0, TIPO_INSCRIPCION)
    return tipos


class ConstanciaPDF(FPDF):
    def __init__(self, titulo):
        super().__init__(format="Letter", unit="mm")
        self.titulo_doc = titulo
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(16, 16, 16)

    def _nl(self, w, h, texto="", **kwargs):
        self.cell(w, h, texto, new_x="LMARGIN", new_y="NEXT", **kwargs)

    def header(self):
        self.set_fill_color(*ROJO)
        self.rect(0, 0, 216, 28, "F")
        logo = Path(settings.BASE_DIR) / "static" / "img" / "logo-blanco.png"
        if logo.exists():
            try:
                self.image(str(logo), x=16, y=7, h=14)
                self.set_xy(40, 8)
            except Exception:
                self.set_xy(16, 8)
        else:
            self.set_xy(16, 8)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self._nl(0, 7, "INGENIO")
        self.set_x(40 if logo.exists() else 16)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, _txt(self.titulo_doc))
        self.ln(18)
        self.set_text_color(*NEGRO)

    def footer(self):
        self.set_y(-16)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(
            0,
            5,
            _txt("Constancia interna de Ingenio. No es certificado de terminacion ni titulo."),
            align="C",
        )


def construir_constancia(alumno, tipo):
    tipo = tipo if tipo in (TIPO_INSCRIPCION, TIPO_HISTORIAL) else TIPO_HISTORIAL
    if tipo == TIPO_INSCRIPCION and not es_alumno_regular(alumno):
        tipo = TIPO_HISTORIAL
    titulo = (
        "Constancia de inscripcion"
        if tipo == TIPO_INSCRIPCION
        else "Constancia de historial academico"
    )
    pdf = ConstanciaPDF(titulo)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf._nl(0, 8, _txt(titulo))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS)
    pdf._nl(0, 5, f"Fecha de emision: {timezone.localdate().strftime('%d/%m/%Y')}")
    pdf.set_text_color(*NEGRO)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf._nl(0, 7, "Alumno")
    pdf.set_font("Helvetica", "", 10)
    pdf._nl(0, 6, _txt(f"Nombre: {alumno.nombre} {alumno.apellido}"))
    pdf._nl(0, 6, _txt(f"CURP: {alumno.curp}"))
    pdf._nl(0, 6, _txt(f"Codigo Ingenio: {alumno.codigo_ingenio or alumno.pk}"))
    pdf._nl(0, 6, _txt(f"Estado del expediente: {alumno.estado}"))
    pdf.ln(3)
    qs = inscripciones_de(alumno)
    if tipo == TIPO_INSCRIPCION:
        qs = qs.filter(estado="activo")
        pdf.set_font("Helvetica", "", 10)
        pdf._nl(0, 6, _txt("Se hace constar que la persona esta inscrita en Ingenio en el periodo vigente, con las materias siguientes."))
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf._nl(0, 6, _txt("Historial de inscripciones en Ingenio. No acredita conclusion de estudios."))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(70, 6, "Curso", border="B")
    pdf.cell(40, 6, "Periodo", border="B")
    pdf.cell(30, 6, "Estado", border="B")
    pdf._nl(0, 6, "Calif.", border="B", align="R")
    pdf.set_font("Helvetica", "", 9)
    filas = list(qs)
    if not filas:
        pdf._nl(0, 6, "Sin inscripciones.")
    for ins in filas:
        nota = "-" if ins.calificacion is None else str(ins.calificacion)
        pdf.cell(70, 6, _txt(ins.curso.nombre)[:38])
        pdf.cell(40, 6, _txt(ins.periodo.nombre)[:18])
        pdf.cell(30, 6, _txt(ins.estado))
        pdf._nl(0, 6, nota, align="R")
    return bytes(pdf.output()), tipo
