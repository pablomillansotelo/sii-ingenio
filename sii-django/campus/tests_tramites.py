import re
import zlib
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse


def pdf_texto(raw):
    partes = []
    for blob in re.findall(rb"stream\r?\n(.+?)\r?\nendstream", raw, re.S):
        try:
            partes.append(zlib.decompress(blob))
        except Exception:
            partes.append(blob)
    return b"\n".join(partes)

from campus.services.constancia import tipos_disponibles
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ADMINISTRADOR, GRUPO_ALUMNO, crear_grupos


class CampusConstanciaTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("cons1", "cons1@example.com", "secret123")
        self.otro = User.objects.create_user("cons2", "cons2@example.com", "secret123")
        self.admin = User.objects.create_user("consadm", "consadm@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMINISTRADOR))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Luz",
            apellido="Constancia",
            email="cons1@example.com",
            curp="COLU000101MDFXXX12",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.ajeno = Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otro",
            apellido="Constancia",
            email="cons2@example.com",
            curp="COOT000101HDFXXX12",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.periodo = Periodo.objects.create(
            nombre="2026-A", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 6, 30)
        )
        self.curso = Curso.objects.create(nombre="Álgebra")
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)
        self.http_admin = Client()
        self.http_admin.force_login(self.admin)

    def test_regular_puede_inscripcion_e_historial(self):
        Inscripcion.objects.create(
            alumno=self.alumno, curso=self.curso, periodo=self.periodo, estado="activo"
        )
        self.assertIn("inscripcion", tipos_disponibles(self.alumno))
        pagina = self.http.get(reverse("campus_constancias"))
        self.assertContains(pagina, "constancia de inscripción")
        pdf = self.http.get(reverse("campus_constancia_pdf") + "?tipo=inscripcion")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        cuerpo = pdf_texto(pdf.content)
        self.assertIn(b"Luz", cuerpo)
        self.assertIn(b"COLU000101MDFXXX12", cuerpo)
        self.assertIn(b"INGENIO", cuerpo)

    def test_baja_total_solo_historial(self):
        Inscripcion.objects.create(
            alumno=self.alumno, curso=self.curso, periodo=self.periodo, estado="cancelado"
        )
        self.assertNotIn("inscripcion", tipos_disponibles(self.alumno))
        pagina = self.http.get(reverse("campus_constancias"))
        self.assertContains(pagina, "solo se emite historial")
        pdf = self.http.get(reverse("campus_constancia_pdf") + "?tipo=inscripcion")
        self.assertIn(b"historial", pdf_texto(pdf.content).lower())
        self.assertIn(b"constancia-historial-", pdf["Content-Disposition"].encode())

    def test_alumno_no_descarga_la_de_otro(self):
        Inscripcion.objects.create(
            alumno=self.ajeno, curso=self.curso, periodo=self.periodo, estado="activo"
        )
        pdf = self.http.get(reverse("campus_constancia_pdf") + "?tipo=historial")
        self.assertNotIn(b"COOT000101HDFXXX12", pdf_texto(pdf.content))
        ajeno = self.http_otro.get(reverse("sii_constancia_pdf", args=[self.alumno.pk]))
        self.assertIn(ajeno.status_code, (403, 404))

    def test_staff_descarga_constancia_de_alumno(self):
        Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso,
            periodo=self.periodo,
            estado="completado",
            calificacion=Decimal("9.00"),
        )
        pdf = self.http_admin.get(reverse("sii_constancia_pdf", args=[self.alumno.pk]))
        self.assertEqual(pdf.status_code, 200)
        plano = pdf_texto(pdf.content)
        self.assertIn(b"Luz", plano)
        self.assertIn(b"COLU000101MDFXXX12", plano)
