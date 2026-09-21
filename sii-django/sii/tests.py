from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.staticfiles import finders
from django.test import Client, TestCase
from django.urls import reverse

from docente.models import Docente, DocenteCurso
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_DOCENTE, crear_grupos
from ventas.models import Cliente, Producto, Venta, VentaDetalle


class SiiOperacionTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "secret123")
        self.docente_user = User.objects.create_user("profe", "profe@example.com", "secret123")
        self.docente_user.groups.add(Group.objects.get(name=GRUPO_DOCENTE))
        self.http_admin = Client()
        self.http_admin.login(username="admin", password="secret123")
        self.http_profe = Client()
        self.http_profe.login(username="profe", password="secret123")

    def test_alta_alumno_sin_cliente(self):
        response = self.http_admin.post(
            reverse("sii_alumno_crear"),
            {
                "nombre": "Eva",
                "apellido": "Ruiz",
                "email": "eva.sii@example.com",
                "curp": "RUEV000101MDFXXX01",
                "fecha_nacimiento": "2000-01-01",
                "estado": "activo",
            },
        )
        self.assertRedirects(response, reverse("sii_alumnos"))
        self.assertTrue(Alumno.objects.filter(email="eva.sii@example.com").exists())

    def test_docente_no_crea_alumno(self):
        self.http_profe.post(
            reverse("sii_alumno_crear"),
            {
                "nombre": "No",
                "apellido": "Debe",
                "email": "nodebe@example.com",
                "curp": "XXXX000101HDFXXX09",
                "fecha_nacimiento": "2000-01-01",
                "estado": "activo",
            },
        )
        self.assertFalse(Alumno.objects.filter(email="nodebe@example.com").exists())

    def test_baja_y_reintento_inscripcion(self):
        alumno = Alumno.objects.create(
            nombre="Luis",
            apellido="Perez",
            email="luis.sii@example.com",
            curp="PELU000101HDFXXX02",
            fecha_nacimiento=date(2000, 1, 1),
        )
        curso = Curso.objects.create(nombre="Historia")
        periodo = Periodo.objects.create(
            nombre="2026-A", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 6, 30)
        )
        inscripcion = Inscripcion.objects.create(alumno=alumno, curso=curso, periodo=periodo)
        baja = self.http_admin.post(reverse("sii_inscripcion_baja"), {"id_inscripcion": inscripcion.pk})
        self.assertRedirects(baja, reverse("sii_inscripciones"))
        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estado, "cancelado")
        reintento = self.http_admin.post(
            reverse("sii_inscripcion_reintento"), {"id_inscripcion": inscripcion.pk}
        )
        self.assertRedirects(reintento, reverse("sii_inscripciones"))
        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estado, "activo")
        self.assertEqual(inscripcion.intento, 2)

    def test_asignar_docente_a_curso(self):
        docente = Docente.objects.create(
            nombre="Marta", apellido="Gil", email="marta.sii@example.com"
        )
        curso = Curso.objects.create(nombre="Literatura")
        response = self.http_admin.post(
            reverse("sii_asignacion_crear"),
            {"docente": docente.pk, "curso": curso.pk},
        )
        self.assertRedirects(response, reverse("sii_docentes"))
        self.assertTrue(DocenteCurso.objects.filter(docente=docente, curso=curso).exists())


class InicioEscritorioTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "secret123")
        self.http = Client()
        self.http.login(username="admin", password="secret123")
        cliente = Cliente.objects.create(
            nombre="Ana",
            apellidos="Lopez",
            direccion="Calle 1",
            email="ana.home@example.com",
        )
        producto = Producto.objects.create(producto="Inglés", precio_unitario=Decimal("1000"), activo=True)
        venta = Venta.objects.create(id_cliente=cliente, fecha=date.today(), estado_pago="pendiente")
        VentaDetalle.objects.create(
            id_venta=venta,
            id_producto=producto,
            cantidad=1,
            precio_unitario=Decimal("1000"),
        )

    def test_inicio_es_escritorio_no_menu(self):
        response = self.http.get(reverse("inicio"))
        self.assertContains(response, "Hoy")
        self.assertContains(response, "Nueva venta")
        self.assertNotContains(response, "Entrar a Ventas")
        self.assertNotContains(response, "Entrar a SII")
        self.assertNotContains(response, "Accesos rápidos")
        self.assertContains(response, "Pagos pendientes")
        self.assertContains(response, "Control escolar")
        self.assertContains(response, "Fecha")
        self.assertContains(response, "Total")
        self.assertContains(response, "por cobrar")
        self.assertContains(response, "Registrar pago")
        self.assertContains(response, "table-row-link")
        self.assertContains(response, "img/logo-blanco.png")
        self.assertContains(response, "bi-list")
        self.assertContains(response, 'id="sidebarIngenio"')
        self.assertContains(response, "sidebar-link")
        self.assertContains(response, "text-bg-warning")

    def test_ventas_usa_sidebar_no_dropdown_de_seccion(self):
        response = self.http.get(reverse("ventas_home"))
        self.assertContains(response, "Punto de venta")
        self.assertContains(response, "Folios")
        self.assertContains(response, 'id="sidebarIngenio"')
        self.assertNotContains(response, "Accesos rápidos")
        self.assertContains(response, "stat-card")

    def test_pos_es_tres_pasos(self):
        response = self.http.get(reverse("Carrito"))
        self.assertContains(response, "pos-steps")
        self.assertContains(response, "Cliente")
        self.assertContains(response, "Cursos")
        self.assertContains(response, "Confirmar")
        self.assertContains(response, "pos-step-num")

    def test_sii_home_solo_control_escolar(self):
        response = self.http.get(reverse("sii_home"))
        self.assertContains(response, "Alumnos")
        self.assertContains(response, "Periodos")
        self.assertNotContains(response, "Cursos en venta")
        self.assertNotContains(response, "Últimas ventas")
        self.assertContains(response, "stat-card")

    def test_tablas_tienen_busqueda(self):
        for name, table_id in (
            ("Ventas", "tabla-folios"),
            ("Clientes", "tabla-clientes"),
            ("Pagos", "tabla-pagos"),
            ("sii_alumnos", "tabla-alumnos"),
        ):
            response = self.http.get(reverse(name))
            self.assertContains(response, f'data-table-search="{table_id}"')
            self.assertContains(response, f'id="{table_id}"')


class StaticFilesProduccionTests(TestCase):
    """Vercel sirve /static/* desde STATIC_ROOT; si falta un archivo se ve el HTML crudo."""

    databases = {"default", "auth"}

    REQUIRED = (
        "css/main.css",
        "js/carrito.js",
        "js/shell.js",
        "img/logo.png",
        "img/logo.ico",
        "img/logo-blanco.png",
    )

    def test_whitenoise_esta_activo(self):
        self.assertEqual(settings.MIDDLEWARE[1], "whitenoise.middleware.WhiteNoiseMiddleware")

    def test_fuentes_de_desarrollo_existen(self):
        for rel in self.REQUIRED:
            self.assertTrue(finders.find(rel), f"No está en static/: {rel}")

    def test_staticfiles_publicado_incluye_marca(self):
        root = Path(settings.STATIC_ROOT)
        for rel in self.REQUIRED:
            self.assertTrue((root / rel).is_file(), f"Falta {rel} en staticfiles/. Corre collectstatic.")

    def test_login_referencia_assets(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "css/main.css")
        self.assertContains(response, "img/logo-blanco.png")
        self.assertContains(response, "img/logo.ico")


class RbacFase0Tests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        from sii.identity import asignar_grupos_desde_dominio
        from sii.permissions import GRUPO_ALUMNO, GRUPO_VENDEDOR
        from ventas.models import Vendedor

        crear_grupos()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "secret123")
        self.alum_user = User.objects.create_user("alum", "alum.rbac@example.com", "secret123")
        self.vend_user = User.objects.create_user("vend", "vend.rbac@example.com", "secret123")
        self.alum_user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.vend_user.groups.add(Group.objects.get(name=GRUPO_VENDEDOR))
        self.alumno = Alumno.objects.create(
            user_id=self.alum_user.pk,
            nombre="Ana",
            apellido="Rbac",
            email="alum.rbac@example.com",
            curp="RBAN000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.cliente = Cliente.objects.create(
            nombre="Ana",
            apellidos="Rbac",
            direccion="Calle 1",
            email="alum.rbac@example.com",
            id_alumno_sii=self.alumno,
        )
        self.venta_propia = Venta.objects.create(
            id_cliente=self.cliente, fecha=date.today(), estado_pago="pendiente"
        )
        ajeno = Cliente.objects.create(
            nombre="Otro",
            apellidos="Cliente",
            direccion="Calle 2",
            email="otro.rbac@example.com",
        )
        self.venta_ajena = Venta.objects.create(
            id_cliente=ajeno, fecha=date.today(), estado_pago="pagado"
        )
        Vendedor.objects.create(
            user_id=self.vend_user.pk,
            nombre="Vend Rbac",
            email="vend.rbac@example.com",
        )
        asignar_grupos_desde_dominio()
        self.http_alum = Client()
        self.http_alum.login(username="alum", password="secret123")
        self.http_vend = Client()
        self.http_vend.login(username="vend", password="secret123")
        self.http_admin = Client()
        self.http_admin.login(username="admin", password="secret123")

    def test_middleware_es_por_feature(self):
        self.assertIn("sii.middleware.FeatureAccessMiddleware", settings.MIDDLEWARE)

    def test_alumno_403_en_pos(self):
        response = self.http_alum.get(reverse("Carrito"))
        self.assertEqual(response.status_code, 403)

    def test_alumno_200_en_mis_compras(self):
        response = self.http_alum.get(reverse("mis_compras"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis compras")
        self.assertContains(response, self.venta_propia.folio or str(self.venta_propia.pk))
        self.assertNotContains(response, self.venta_ajena.folio or str(self.venta_ajena.pk))

    def test_alumno_recibo_propio_y_ajeno(self):
        propio = self.http_alum.get(reverse("recibo", args=[self.venta_propia.pk]))
        self.assertEqual(propio.status_code, 200)
        self.assertContains(propio, self.venta_propia.folio or str(self.venta_propia.pk))
        ajeno = self.http_alum.get(reverse("recibo", args=[self.venta_ajena.pk]))
        self.assertEqual(ajeno.status_code, 404)

    def test_alumno_kardex_en_sii(self):
        response = self.http_alum.get(reverse("sii_kardex"))
        self.assertEqual(response.status_code, 200)
        aula = self.http_alum.get(reverse("aula_dashboard"))
        self.assertNotContains(aula, "Kardex")

    def test_alumno_menu_sin_pos_ni_cobro(self):
        response = self.http_alum.get(reverse("inicio"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Nueva venta")
        self.assertNotContains(response, "Punto de venta")
        self.assertNotContains(response, "Registrar pago")
        self.assertNotContains(response, "por cobrar")
        self.assertContains(response, "Mis compras")
        self.assertContains(response, "Kardex")

    def test_vendedor_403_en_calificar(self):
        response = self.http_vend.get(reverse("aula_calificar", args=[1]))
        self.assertEqual(response.status_code, 403)

    def test_superusuario_entra_al_pos(self):
        response = self.http_admin.get(reverse("Carrito"))
        self.assertEqual(response.status_code, 200)

    def test_union_vendedor_y_docente(self):
        from sii.identity import asignar_grupos_desde_dominio, roles_inferidos
        from sii.permissions import GRUPO_DOCENTE, GRUPO_VENDEDOR
        from sii.rbac import has_feature

        Docente.objects.create(
            user_id=self.vend_user.pk,
            nombre="Vend",
            apellido="Profe",
            email="vend.rbac@example.com",
        )
        asignar_grupos_desde_dominio()
        self.vend_user.refresh_from_db()
        for attr in ("_ingenio_roles", "_ingenio_features"):
            if hasattr(self.vend_user, attr):
                delattr(self.vend_user, attr)
        nombres = set(self.vend_user.groups.values_list("name", flat=True))
        self.assertIn(GRUPO_VENDEDOR, nombres)
        self.assertIn(GRUPO_DOCENTE, nombres)
        self.vend_user = User.objects.get(pk=self.vend_user.pk)
        self.assertEqual(roles_inferidos(self.vend_user), {GRUPO_VENDEDOR, GRUPO_DOCENTE})
        self.assertTrue(has_feature(self.vend_user, "ventas.pos"))
        self.assertTrue(has_feature(self.vend_user, "aula.calificar"))

