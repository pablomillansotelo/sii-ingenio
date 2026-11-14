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


class CampusBajaTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        from ventas.models import EdicionCurso, Producto

        crear_grupos()
        self.user = User.objects.create_user("baja1", "baja1@example.com", "secret123")
        self.otro = User.objects.create_user("baja2", "baja2@example.com", "secret123")
        self.admin = User.objects.create_user("bajaadm", "bajaadm@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMINISTRADOR))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Beto",
            apellido="Baja",
            email="baja1@example.com",
            curp="BAJA000101HDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.ajeno = Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otra",
            apellido="Baja",
            email="baja2@example.com",
            curp="BAOT000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.periodo = Periodo.objects.create(
            nombre="2026-B", fecha_inicio=date(2026, 7, 1), fecha_fin=date(2026, 12, 15)
        )
        self.curso = Curso.objects.create(nombre="Cálculo")
        producto = Producto.objects.create(
            producto="Cálculo", precio_unitario=Decimal("1000"), id_curso=self.curso
        )
        self.edicion = EdicionCurso.objects.create(
            id_curso=producto,
            codigo_edicion="CAL-A",
            fecha_inicio=self.periodo.fecha_inicio,
            fecha_fin=self.periodo.fecha_fin,
            cupo_maximo=20,
            cupo_ocupado=1,
        )
        self.ins = Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso,
            periodo=self.periodo,
            estado="activo",
            id_edicion=self.edicion,
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)
        self.http_admin = Client()
        self.http_admin.force_login(self.admin)

    def test_solicitud_no_aplica_baja_hasta_aprobar(self):
        from sii.models import SolicitudBaja

        pagina = self.http.get(reverse("campus_bajas"))
        self.assertContains(pagina, "Cálculo")
        self.assertContains(pagina, reverse("campus_bajas"))
        hub = self.http.get(reverse("campus_control_escolar"))
        self.assertContains(hub, reverse("campus_bajas"))
        self.http.post(
            reverse("campus_bajas"),
            {"inscripcion_id": self.ins.pk, "motivo": "Cambio de horario"},
        )
        self.ins.refresh_from_db()
        self.edicion.refresh_from_db()
        self.assertEqual(self.ins.estado, "activo")
        self.assertEqual(self.edicion.cupo_ocupado, 1)
        sol = SolicitudBaja.objects.get(inscripcion=self.ins)
        self.assertEqual(sol.estado, SolicitudBaja.ESTADO_ENVIADA)
        self.assertEqual(sol.creada_por_id, self.user.pk)
        ajeno = self.http_otro.post(
            reverse("campus_bajas"),
            {"inscripcion_id": self.ins.pk, "motivo": "No es mía"},
        )
        self.assertEqual(ajeno.status_code, 404)
        self.http_admin.post(
            reverse("sii_solicitud_baja_resolver", args=[sol.pk]),
            {"decision": "aprobar"},
        )
        self.ins.refresh_from_db()
        self.edicion.refresh_from_db()
        sol.refresh_from_db()
        self.assertEqual(self.ins.estado, "cancelado")
        self.assertFalse(self.ins.puede_cursar)
        self.assertEqual(self.edicion.cupo_ocupado, 0)
        self.assertEqual(sol.estado, SolicitudBaja.ESTADO_APROBADA)
        lista = self.http.get(reverse("campus_bajas"))
        self.assertContains(lista, "Aprobada")
