"""Recibo interno: lookup compartido y PDF. No es CFDI."""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings
from django.http import Http404
from fpdf import FPDF

from sii.identity import ventas_visibles
from sii.rbac import has_any_feature

ROJO = (206, 14, 45)
GRIS = (90, 90, 90)
NEGRO = (33, 33, 33)
FONDO = (248, 246, 246)


def venta_para_recibo(user, venta_id):
    if not has_any_feature(user, ("ventas.mis_compras", "ventas.folios")):
        raise Http404()
    venta = (
        ventas_visibles(user)
        .select_related("id_cliente", "id_vendedor")
        .prefetch_related("ventadetalle_set__id_producto", "ventadetalle_set__id_edicion", "pagos")
        .filter(pk=venta_id)
        .first()
    )
    if venta is None:
        raise Http404()
    return venta


def _txt(value, vacio="-"):
    if value is None or value == "":
        return vacio
    texto = str(value)
    for origen, destino in (
        ("—", "-"),
        ("–", "-"),
        ("“", '"'),
        ("”", '"'),
        ("‘", "'"),
        ("’", "'"),
        ("•", "-"),
    ):
        texto = texto.replace(origen, destino)
    return texto.encode("latin-1", "replace").decode("latin-1")


def _mxn(valor):
    cuantia = Decimal(valor or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"${cuantia:,.2f}"


def _fecha(valor, con_hora=False):
    if not valor:
        return "-"
    if con_hora:
        return valor.strftime("%d/%m/%Y %H:%M")
    return valor.strftime("%d/%m/%Y")


class ReciboPDF(FPDF):
    def __init__(self, venta):
        super().__init__(format="Letter", unit="mm")
        self.venta = venta
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
        self.cell(0, 6, "Comprobante interno  |  No es factura fiscal")
        self.ln(18)
        self.set_text_color(*NEGRO)

    def footer(self):
        self.set_y(-16)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(
            0,
            5,
            _txt("Documento interno de Ingenio. No sustituye un CFDI."),
            align="C",
        )


def construir_pdf(venta) -> bytes:
    detalles = list(venta.ventadetalle_set.all())
    pagos = list(venta.pagos.all())
    total = Decimal(venta.monto or 0)
    pagado = sum((pago.monto for pago in pagos), Decimal("0"))
    saldo = total - pagado
    cliente = venta.id_cliente
    folio = venta.folio or str(venta.pk)

    pdf = ReciboPDF(venta)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf._nl(0, 8, _txt(f"Recibo {folio}"))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS)
    pdf._nl(0, 5, f"Estado de pago: {_txt(venta.get_estado_pago_display())}")
    pdf.set_text_color(*NEGRO)
    pdf.ln(3)

    pdf.set_fill_color(*FONDO)
    pdf.set_font("Helvetica", "B", 10)
    pdf._nl(0, 7, "Cliente", fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, _txt(cliente))
    pdf._nl(0, 6, f"Fecha: {_fecha(venta.fecha)}")
    pdf.cell(95, 6, _txt(cliente.email if cliente else ""))
    pdf._nl(0, 6, _txt(f"Vendedor: {venta.vendedor_nombre}"))
    if cliente and cliente.telefono:
        pdf._nl(0, 6, _txt(f"Telefono: {cliente.telefono}"))
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf._nl(0, 7, "Cursos", fill=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(78, 6, "Curso", border="B")
    pdf.cell(42, 6, "Edicion", border="B")
    pdf.cell(22, 6, "Plazas", border="B", align="R")
    pdf._nl(0, 6, "Importe", border="B", align="R")
    pdf.set_font("Helvetica", "", 9)
    if not detalles:
        pdf._nl(0, 6, "Sin lineas.")
    for det in detalles:
        edicion = det.id_edicion.codigo_edicion if det.id_edicion_id else "-"
        pdf.cell(78, 6, _txt(det.id_producto)[:40])
        pdf.cell(42, 6, _txt(edicion)[:20])
        pdf.cell(22, 6, str(det.cantidad), align="R")
        pdf._nl(0, 6, _mxn(det.subtotal()), align="R")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(142, 7, "Total", align="R")
    pdf._nl(0, 7, _mxn(total), align="R")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf._nl(0, 7, "Pagos aplicados", fill=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(40, 6, "Fecha", border="B")
    pdf.cell(40, 6, "Metodo", border="B")
    pdf.cell(52, 6, "Referencia", border="B")
    pdf._nl(0, 6, "Monto", border="B", align="R")
    pdf.set_font("Helvetica", "", 9)
    if not pagos:
        pdf._nl(0, 6, _txt(f"Aun no hay pagos. El folio sigue {venta.get_estado_pago_display()}."))
    for pago in pagos:
        pdf.cell(40, 6, _fecha(pago.fecha_pago, con_hora=True))
        pdf.cell(40, 6, _txt(pago.metodo))
        pdf.cell(52, 6, _txt(pago.referencia or "-")[:28])
        pdf._nl(0, 6, _mxn(pago.monto), align="R")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(142, 7, "Pagado", align="R")
    pdf._nl(0, 7, _mxn(pagado), align="R")
    pdf.cell(142, 7, "Saldo", align="R")
    pdf._nl(0, 7, _mxn(saldo), align="R")

    return bytes(pdf.output())
