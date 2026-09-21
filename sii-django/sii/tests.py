from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.staticfiles import finders
from django.test import Client, TestCase
from django.urls import reverse

from docente.models import Docente, DocenteCurso
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_DOCENTE, crear_grupos


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


class StaticFilesProduccionTests(TestCase):
    """Vercel sirve /static/* desde STATIC_ROOT; si falta un archivo se ve el HTML crudo."""

    databases = {"default", "auth"}

    REQUIRED = (
        "css/main.css",
        "js/carrito.js",
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

