from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from sii.models import Inscripcion
from sii.permissions import GRUPO_VENDEDOR, crear_grupos
from ventas.models import Cliente, EdicionCurso, Producto, Venta, VentaDetalle
from ventas.services import asegurar_curso_para_producto, inscribir_desde_venta


class DominioVentaInscripcionTests(TestCase):
    databases = {"default", "auth"}

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


class EdicionCursoTests(TestCase):
    databases = {"default", "auth"}

    def test_reservar_y_liberar_cupo(self):
        producto = Producto.objects.create(producto="Django", precio_unitario=Decimal("200"))
        edicion = EdicionCurso.objects.create(
            id_curso=producto,
            codigo_edicion="DJ-01-2026",
            fecha_inicio=date.today() + timedelta(days=7),
            cupo_maximo=10,
        )
        edicion.reservar_cupo(2)
        edicion.refresh_from_db()
        self.assertEqual(edicion.cupo_ocupado, 2)
        self.assertEqual(edicion.cupo_disponible, 8)
        edicion.liberar_cupo(2)
        edicion.refresh_from_db()
        self.assertEqual(edicion.cupo_ocupado, 0)


class VentaViewTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user(username="asesor", password="secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_VENDEDOR))
        self.http = Client()
        self.http.login(username="asesor", password="secret123")
        self.cliente = Cliente.objects.create(
            nombre="Luis",
            apellidos="Perez",
            direccion="Calle 2",
            email="luis.pos@example.com",
            activo=True,
        )

    def test_dashboard_view(self):
        response = self.http.get(reverse("ventas_home"))
        self.assertEqual(response.status_code, 200)

    def test_add_carrito_asigna_vendedor_y_crea_inscripcion(self):
        producto = Producto.objects.create(
            producto="Django",
            precio_unitario=Decimal("200"),
            activo=True,
        )
        response = self.http.post(
            reverse("AddCarrito"),
            {
                "id_cliente_add": self.cliente.id_cliente,
                "fecha_add": "2025-08-11",
                "observaciones_add": "",
                "nplainArray[]": f"{producto.id_producto},,1,0",
            },
        )
        self.assertRedirects(response, reverse("Ventas"))
        venta = Venta.objects.latest("id_venta")
        self.assertEqual(venta.id_vendedor.user_id, self.user.id)
        self.assertTrue(venta.folio.startswith("V-"))
        self.assertEqual(Inscripcion.objects.filter(alumno__email=self.cliente.email).count(), 1)

    def test_add_carrito_con_edicion_reserva_cupo(self):
        producto = Producto.objects.create(
            producto="UX",
            precio_unitario=Decimal("150"),
            activo=True,
        )
        edicion = EdicionCurso.objects.create(
            id_curso=producto,
            codigo_edicion="UX-01-2026",
            fecha_inicio=date.today(),
            cupo_maximo=5,
            estado=EdicionCurso.ESTADO_PROGRAMADA,
            activo=True,
        )
        response = self.http.post(
            reverse("AddCarrito"),
            {
                "id_cliente_add": self.cliente.id_cliente,
                "fecha_add": "2025-08-11",
                "nplainArray[]": f"{producto.id_producto},{edicion.id_edicion},1,0",
            },
        )
        self.assertRedirects(response, reverse("Ventas"))
        edicion.refresh_from_db()
        self.assertEqual(edicion.cupo_ocupado, 1)

    def test_add_carrito_exige_edicion_si_hay_cupo(self):
        producto = Producto.objects.create(
            producto="Data",
            precio_unitario=Decimal("90"),
            activo=True,
        )
        EdicionCurso.objects.create(
            id_curso=producto,
            codigo_edicion="DATA-01",
            fecha_inicio=date.today(),
            cupo_maximo=3,
            activo=True,
        )
        response = self.http.post(
            reverse("AddCarrito"),
            {
                "id_cliente_add": self.cliente.id_cliente,
                "fecha_add": "2025-08-11",
                "nplainArray[]": f"{producto.id_producto},,1,0",
            },
        )
        self.assertRedirects(response, reverse("Carrito"))
        self.assertEqual(Venta.objects.count(), 0)

    def test_delete_venta_libera_cupo(self):
        producto = Producto.objects.create(producto="Libro", precio_unitario=Decimal("50"), activo=True)
        edicion = EdicionCurso.objects.create(
            id_curso=producto,
            codigo_edicion="BK-01",
            fecha_inicio=date.today(),
            cupo_maximo=4,
            cupo_ocupado=1,
            activo=True,
        )
        venta = Venta.objects.create(id_cliente=self.cliente, fecha=date.today())
        VentaDetalle.objects.create(
            id_venta=venta,
            id_producto=producto,
            id_edicion=edicion,
            cantidad=1,
            precio_unitario=Decimal("50"),
        )
        response = self.http.post(reverse("DeleteVenta"), {"id_venta_eliminar": venta.id_venta})
        self.assertRedirects(response, reverse("Ventas"))
        self.assertFalse(Venta.objects.filter(pk=venta.pk).exists())
        edicion.refresh_from_db()
        self.assertEqual(edicion.cupo_ocupado, 0)

    def test_pagos_view(self):
        response = self.http.get(reverse("Pagos"))
        self.assertEqual(response.status_code, 200)
