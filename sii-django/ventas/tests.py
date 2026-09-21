from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from sii.models import Inscripcion
from sii.permissions import GRUPO_VENDEDOR, crear_grupos
from ventas.models import Cliente, EdicionCurso, Pago, Producto, Venta, VentaDetalle, Vendedor
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
        self.assertEqual(creadas.creadas, 1)
        inscripcion = Inscripcion.objects.get(curso=producto.id_curso)
        self.assertEqual(inscribir_desde_venta(venta).ya_inscritas, 1)
        self.assertFalse(inscripcion.puede_cursar)

    def test_inscripcion_apunta_a_edicion_y_baja_libera_cupo(self):
        producto = Producto.objects.create(producto="UX", precio_unitario=Decimal("150"))
        edicion = EdicionCurso.objects.create(
            id_curso=producto,
            codigo_edicion="UX-01-2026",
            fecha_inicio=date.today(),
            cupo_maximo=5,
            cupo_ocupado=1,
        )
        cliente = Cliente.objects.create(
            nombre="Ana", apellidos="López", direccion="Calle 1", email="ana.edicion@example.com"
        )
        venta = Venta.objects.create(id_cliente=cliente, fecha=date.today(), estado="confirmada")
        VentaDetalle.objects.create(
            id_venta=venta,
            id_producto=producto,
            id_edicion=edicion,
            cantidad=1,
            precio_unitario=Decimal("150"),
        )
        resultado = inscribir_desde_venta(venta)
        self.assertEqual(resultado.creadas, 1)
        inscripcion = Inscripcion.objects.get()
        self.assertEqual(inscripcion.id_edicion_id, edicion.pk)
        inscripcion.dar_baja()
        edicion.refresh_from_db()
        self.assertEqual(edicion.cupo_ocupado, 0)

    def test_cantidad_mayor_a_uno_no_clona_inscripciones(self):
        producto = Producto.objects.create(producto="Grupo", precio_unitario=Decimal("80"))
        cliente = Cliente.objects.create(
            nombre="Ana", apellidos="López", direccion="Calle 1", email="ana.cant@example.com"
        )
        venta = Venta.objects.create(id_cliente=cliente, fecha=date.today(), estado="confirmada")
        VentaDetalle.objects.create(
            id_venta=venta,
            id_producto=producto,
            cantidad=3,
            precio_unitario=Decimal("80"),
        )
        self.assertEqual(inscribir_desde_venta(venta).creadas, 1)
        self.assertEqual(Inscripcion.objects.count(), 1)

    def test_historial_por_periodo(self):
        producto = Producto.objects.create(producto="Historia", precio_unitario=Decimal("10"))
        cliente = Cliente.objects.create(
            nombre="Ana", apellidos="López", direccion="Calle 1", email="ana.hist@example.com"
        )
        venta = Venta.objects.create(
            id_cliente=cliente, fecha=date(2025, 3, 1), estado="confirmada", estado_pago="pagado"
        )
        VentaDetalle.objects.create(
            id_venta=venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("10")
        )
        self.assertEqual(inscribir_desde_venta(venta).creadas, 1)
        venta2 = Venta.objects.create(
            id_cliente=cliente, fecha=date(2026, 3, 1), estado="confirmada", estado_pago="pagado"
        )
        VentaDetalle.objects.create(
            id_venta=venta2, id_producto=producto, cantidad=1, precio_unitario=Decimal("10")
        )
        self.assertEqual(inscribir_desde_venta(venta2).creadas, 1)
        self.assertEqual(Inscripcion.objects.filter(alumno__email=cliente.email).count(), 2)

    def test_editar_cliente_actualiza_alumno(self):
        cliente = Cliente.objects.create(
            nombre="Ana", apellidos="López", direccion="Calle 1", email="ana.sync@example.com"
        )
        alumno = cliente.id_alumno_sii
        self.assertIsNotNone(alumno)
        cliente.nombre = "Anita"
        cliente.save()
        alumno.refresh_from_db()
        self.assertEqual(alumno.nombre, "Anita")

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
        self.user = User.objects.create_user("asesor", "asesor@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_VENDEDOR))
        Vendedor.objects.create(user_id=self.user.pk, nombre="Asesor", email="asesor@example.com")
        self.http = Client()
        self.http.force_login(self.user)
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
        inscripcion = Inscripcion.objects.get(alumno__email=self.cliente.email)
        self.assertFalse(inscripcion.puede_cursar)

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
        inscripcion = Inscripcion.objects.get(alumno__email=self.cliente.email)
        self.assertEqual(inscripcion.id_edicion_id, edicion.pk)

    def test_pago_completa_abre_aula(self):
        producto = Producto.objects.create(producto="Pago", precio_unitario=Decimal("100"), activo=True)
        venta = Venta.objects.create(
            id_cliente=self.cliente, fecha=date.today(), estado="confirmada", estado_pago="pendiente"
        )
        VentaDetalle.objects.create(
            id_venta=venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("100")
        )
        inscribir_desde_venta(venta)
        inscripcion = Inscripcion.objects.get()
        self.assertFalse(inscripcion.puede_cursar)
        Pago.objects.create(id_venta=venta, monto=Decimal("100"), metodo="transferencia")
        venta.actualizar_estado_pago()
        from ventas.services import sincronizar_puede_cursar

        sincronizar_puede_cursar(venta)
        inscripcion.refresh_from_db()
        self.assertTrue(inscripcion.puede_cursar)

    def test_pos_muestra_peek_de_inscripcion(self):
        producto = Producto.objects.create(producto="Inglés", precio_unitario=Decimal("10"), activo=True)
        venta = Venta.objects.create(
            id_cliente=self.cliente, fecha=date.today(), estado="confirmada", estado_pago="pagado"
        )
        VentaDetalle.objects.create(
            id_venta=venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("10")
        )
        inscribir_desde_venta(venta)
        response = self.http.get(reverse("Carrito"))
        self.assertContains(response, "Inglés")
        clientes = self.http.get(reverse("Clientes"))
        self.assertContains(clientes, "Inglés")

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
