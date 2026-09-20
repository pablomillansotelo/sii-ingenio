from datetime import date
from decimal import Decimal

from django.test import TestCase

from sii.models import Curso, Inscripcion
from ventas.models import Cliente, Producto, Venta, VentaDetalle
from ventas.services import asegurar_curso_para_producto, inscribir_desde_venta


class DominioVentaInscripcionTests(TestCase):
    def test_producto_crea_curso_y_venta_inscribe(self):
        producto = Producto.objects.create(
            producto="Curso de prueba",
            precio_unitario=Decimal("100.0000"),
            descripcion="Desc",
        )
        producto.refresh_from_db()
        self.assertIsNotNone(producto.id_curso_id)
        self.assertEqual(producto.id_curso.nombre, "Curso de prueba")

        cliente = Cliente.objects.create(
            nombre="Ana",
            apellidos="López",
            direccion="Calle 1",
            email="ana.dominio@example.com",
        )
        venta = Venta.objects.create(
            id_cliente=cliente,
            fecha=date.today(),
            estado="confirmada",
        )
        VentaDetalle.objects.create(
            id_venta=venta,
            id_producto=producto,
            cantidad=1,
            precio_unitario=producto.precio_unitario,
        )
        creadas = inscribir_desde_venta(venta)
        self.assertEqual(creadas, 1)
        self.assertEqual(Inscripcion.objects.filter(curso=producto.id_curso).count(), 1)
        self.assertEqual(inscribir_desde_venta(venta), 0)

    def test_asegurar_curso_reutiliza_el_mismo(self):
        producto = Producto.objects.create(
            producto="Único",
            precio_unitario=Decimal("1.0000"),
        )
        curso_id = asegurar_curso_para_producto(producto).pk
        self.assertEqual(asegurar_curso_para_producto(producto).pk, curso_id)
        self.assertEqual(Curso.objects.filter(nombre="Único").count(), 1)
