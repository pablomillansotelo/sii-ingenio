from datetime import date

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from campus.models import ContactoDirectorio, DocumentoNormativa
from sii.models import Alumno
from sii.permissions import GRUPO_ADMINISTRADOR, GRUPO_ALUMNO, crear_grupos


class CampusNormativaTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("norm1", "norm1@example.com", "secret123")
        self.otro = User.objects.create_user("norm2", "norm2@example.com", "secret123")
        self.admin = User.objects.create_user("normadm", "normadm@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMINISTRADOR))
        Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Nora",
            apellido="Mativa",
            email="norm1@example.com",
            curp="MANO000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_admin = Client()
        self.http_admin.force_login(self.admin)

    def test_borrador_no_se_ve_y_publicado_si(self):
        DocumentoNormativa.objects.create(titulo="Borrador interno", cuerpo="secreto", publicado=False)
        DocumentoNormativa.objects.create(
            titulo="Reglamento de Ingenio",
            cuerpo="Asistencia y evaluación.",
            publicado=True,
            archivo=SimpleUploadedFile("reglamento.pdf", b"%PDF-1.4 x", content_type="application/pdf"),
        )
        ContactoDirectorio.objects.create(
            area="Control escolar", nombre="Ana Mesa", medio="control@ingenio.example", publicado=True
        )
        ContactoDirectorio.objects.create(
            area="Oculto", nombre="No sale", medio="x@y.z", publicado=False
        )
        hub = self.http.get(reverse("campus_control_escolar"))
        self.assertContains(hub, reverse("campus_normativa"))
        self.assertContains(hub, reverse("campus_directorio"))
        pagina = self.http.get(reverse("campus_normativa"))
        self.assertContains(pagina, "Reglamento de Ingenio")
        self.assertNotContains(pagina, "Borrador interno")
        doc = DocumentoNormativa.objects.get(publicado=True)
        self.assertTrue(doc.archivo.name.startswith("normativa/"))
        pdf = self.http.get(reverse("campus_normativa_archivo", args=[doc.pk]))
        self.assertEqual(pdf.status_code, 200)
        directorio = self.http.get(reverse("campus_directorio"))
        self.assertContains(directorio, "Ana Mesa")
        self.assertNotContains(directorio, "No sale")
        self.http_admin.post(
            reverse("sii_normativa"),
            {"accion": "directorio", "area": "Caja", "nombre": "Luis", "medio": "caja@ingenio.example", "publicado": "on"},
        )
        self.assertTrue(ContactoDirectorio.objects.filter(nombre="Luis", publicado=True).exists())


class CampusAyudaTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("ayu1", "ayu1@example.com", "secret123")
        self.otro = User.objects.create_user("ayu2", "ayu2@example.com", "secret123")
        self.admin = User.objects.create_user("ayuadm", "ayuadm@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMINISTRADOR))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Aya",
            apellido="Mesa",
            email="ayu1@example.com",
            curp="MEAY000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otra",
            apellido="Mesa",
            email="ayu2@example.com",
            curp="MEOT000101HDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)
        self.http_admin = Client()
        self.http_admin.force_login(self.admin)

    def test_folio_aislamiento_y_transiciones(self):
        from campus.models import TicketAyuda
        from campus.services.ayuda import puede_transitar

        self.http.post(
            reverse("campus_ayuda"),
            {"categoria": "academico", "asunto": "Kardex", "descripcion": "No veo una materia"},
        )
        ticket = TicketAyuda.objects.get()
        self.assertTrue(ticket.folio.startswith("AYU-"))
        propio = self.http.get(reverse("campus_ayuda_detalle", args=[ticket.pk]))
        self.assertContains(propio, ticket.folio)
        ajeno = self.http_otro.get(reverse("campus_ayuda_detalle", args=[ticket.pk]))
        self.assertEqual(ajeno.status_code, 404)
        self.assertTrue(puede_transitar(TicketAyuda.ESTADO_ABIERTO, TicketAyuda.ESTADO_ATENCION))
        self.assertFalse(puede_transitar(TicketAyuda.ESTADO_CERRADO, TicketAyuda.ESTADO_ABIERTO))
        self.http_admin.post(
            reverse("sii_ayuda_detalle", args=[ticket.pk]),
            {"cuerpo": "Lo revisamos", "estado": "en_atencion"},
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, TicketAyuda.ESTADO_ATENCION)
        self.assertEqual(ticket.respuestas.count(), 1)
        self.http_admin.post(
            reverse("sii_ayuda_detalle", args=[ticket.pk]),
            {"estado": "abierto"},
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, TicketAyuda.ESTADO_ABIERTO)
        self.http_admin.post(
            reverse("sii_ayuda_detalle", args=[ticket.pk]),
            {"estado": "cerrado"},
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, TicketAyuda.ESTADO_CERRADO)
        self.http_admin.post(
            reverse("sii_ayuda_detalle", args=[ticket.pk]),
            {"estado": "en_atencion"},
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, TicketAyuda.ESTADO_CERRADO)


class CampusFacturacionTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("fis1", "fis1@example.com", "secret123")
        self.otro = User.objects.create_user("fis2", "fis2@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Fina",
            apellido="Cal",
            email="fis1@example.com",
            curp="CAFI000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otra",
            apellido="Cal",
            email="fis2@example.com",
            curp="CAOT000101HDFXXX09",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)

    def test_guarda_datos_en_cliente_y_no_es_cfdi(self):
        from ventas.models import Cliente

        pagina = self.http.get(reverse("campus_facturacion"))
        self.assertContains(pagina, "cuando Ingenio emita")
        self.assertContains(pagina, "no es una factura")
        self.assertNotContains(pagina, "Descargar XML")
        malo = self.http.post(
            reverse("campus_facturacion"),
            {"rfc": "x", "razon_social": "A", "codigo_postal_fiscal": "1", "regimen_fiscal": "612"},
        )
        self.assertContains(malo, "RFC")
        self.http.post(
            reverse("campus_facturacion"),
            {
                "rfc": "XAXX010101000",
                "razon_social": "Fina Cal",
                "codigo_postal_fiscal": "06600",
                "regimen_fiscal": "612",
            },
        )
        cliente = Cliente.objects.get(id_alumno_sii=self.alumno)
        self.assertEqual(cliente.rfc, "XAXX010101000")
        self.assertIsNotNone(cliente.factura_solicitada_en)
        ajeno = self.http_otro.get(reverse("campus_facturacion"))
        self.assertNotContains(ajeno, "XAXX010101000")

