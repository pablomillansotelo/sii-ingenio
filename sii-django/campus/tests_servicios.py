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
