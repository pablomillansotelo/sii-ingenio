import shutil
import unittest
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import crear_grupos
from ventas.models import Cliente, Vendedor


def _main_css():
    return Path(settings.BASE_DIR, "static/css/main.css").read_text(encoding="utf-8")


class TableStackCssTests(SimpleTestCase):
    def test_tarjetas_rompen_emails_y_badges(self):
        css = _main_css()
        self.assertIn("overflow-wrap: anywhere", css)
        self.assertIn("minmax(0, 1fr)", css)
        self.assertIn(".table-stack .badge", css)
        self.assertIn("max-width: 100%", css)
        self.assertIn(".table-stack .table-col-name a", css)
        self.assertIn(".table-stack .table-col-email", css)
        bloque = css.split("@media (max-width: 639.98px)")[-1]
        self.assertIn("text-decoration: none", bloque)
        self.assertIn("white-space: normal", bloque)


class TablasLargosEnHtmlTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.admin = User.objects.create_superuser("admin.tablas", "admin.tablas@example.com", "secret123")
        self.http = self.client
        self.http.force_login(self.admin)
        self.alumno = Alumno.objects.create(
            nombre="Fernanda",
            apellido="Yoselin",
            email="Fernanda.yoselin.96@gmail.com",
            curp="YOFE960101MDFXXX01",
            fecha_nacimiento=date(1996, 1, 1),
        )
        self.cliente = Cliente.objects.create(
            nombre="Pablo",
            apellidos="Millan",
            direccion="Calle 1",
            email="pablomillansotelo@icloud.com",
        )
        periodo = Periodo.objects.create(
            nombre="2025-2 Otoño",
            fecha_inicio=date(2025, 8, 1),
            fecha_fin=date(2025, 12, 15),
        )
        curso = Curso.objects.create(nombre="Curso de Marketing Digital")
        peek_alumno = Alumno.objects.get(email="pablomillansotelo@icloud.com")
        Inscripcion.objects.create(alumno=peek_alumno, curso=curso, periodo=periodo)

    def test_alumnos_y_clientes_incluyen_emails_largos(self):
        alumnos = self.http.get(reverse("sii_alumnos"))
        self.assertContains(alumnos, "Fernanda.yoselin.96@gmail.com")
        self.assertContains(alumnos, "table-responsive")
        clientes = self.http.get(reverse("Clientes"))
        self.assertContains(clientes, "pablomillansotelo@icloud.com")
        self.assertContains(clientes, "Curso de Marketing Digital")


def _chrome_bin():
    return shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")


try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - CI no instala playwright
    sync_playwright = None


@unittest.skipUnless(_chrome_bin() and sync_playwright, "requiere Chrome y playwright")
class TablasSinOverflow390Tests(StaticLiveServerTestCase):
    databases = {"default", "auth"}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        crear_grupos()
        cls.admin = User.objects.create_superuser("qa.overflow", "qa.overflow@example.com", "secret123")
        Vendedor.objects.create(user_id=cls.admin.pk, nombre="QA Overflow", email=cls.admin.email)
        alumno = Alumno.objects.create(
            user_id=cls.admin.pk,
            nombre="Fernanda",
            apellido="Yoselin",
            email="Fernanda.yoselin.96@gmail.com",
            curp="YOFE960101MDFXXX02",
            fecha_nacimiento=date(1996, 1, 1),
        )
        Cliente.objects.create(
            nombre="Pablo",
            apellidos="Millan Sotelo",
            direccion="Calle 1",
            email="pablomillansotelo@icloud.com",
            id_alumno_sii=alumno,
        )
        periodo = Periodo.objects.create(
            nombre="2025-2 Otoño",
            fecha_inicio=date(2025, 8, 1),
            fecha_fin=date(2025, 12, 15),
        )
        curso = Curso.objects.create(nombre="Curso de Marketing Digital")
        Inscripcion.objects.create(alumno=alumno, curso=curso, periodo=periodo)

    def test_paginas_de_tablas_no_ensanchan_el_body(self):
        session = self.client
        session.force_login(self.admin)
        cookie = session.cookies[settings.SESSION_COOKIE_NAME].value
        rutas = [
            reverse("ventas_home"),
            reverse("Ventas"),
            reverse("Pagos"),
            reverse("Clientes"),
            reverse("Inventario"),
            reverse("Ediciones"),
            reverse("Vendedores"),
            reverse("sii_inscripciones"),
            reverse("sii_kardex"),
            reverse("sii_actas"),
            reverse("sii_alumnos"),
            reverse("sii_periodos"),
        ]
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=_chrome_bin(), headless=True)
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [{"name": settings.SESSION_COOKIE_NAME, "value": cookie, "url": self.live_server_url}]
            )
            page = context.new_page()
            fallos = []
            for ruta in rutas:
                page.goto(self.live_server_url + ruta, wait_until="networkidle")
                medidas = page.evaluate(
                    """() => {
                      const body = document.body;
                      const html = document.documentElement;
                      return {
                        bodyScroll: body.scrollWidth,
                        bodyClient: body.clientWidth,
                        htmlScroll: html.scrollWidth,
                        htmlClient: html.clientWidth,
                      };
                    }"""
                )
                if medidas["bodyScroll"] > medidas["bodyClient"] + 1:
                    fallos.append(f"{ruta} body {medidas['bodyScroll']} > {medidas['bodyClient']}")
                if medidas["htmlScroll"] > medidas["htmlClient"] + 1:
                    fallos.append(f"{ruta} html {medidas['htmlScroll']} > {medidas['htmlClient']}")
            browser.close()
        self.assertEqual(fallos, [])
