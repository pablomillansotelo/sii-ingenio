from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from aula.models import Actividad, CalificacionActividad
from aula.services import actualizar_kardex
from docente.models import Docente, DocenteCurso
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ALUMNO, GRUPO_DOCENTE, crear_grupos


class AulaActividadTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.periodo = Periodo.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )
        self.curso = Curso.objects.create(nombre="Marketing", descripcion="Grupo A")
        self.alumno_user = User.objects.create_user(username="alum", password="secret123", email="alum@example.com")
        self.docente_user = User.objects.create_user(username="profe", password="secret123", email="profe@example.com")
        self.alumno_user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.docente_user.groups.add(Group.objects.get(name=GRUPO_DOCENTE))
        self.alumno = Alumno.objects.create(
            user_id=self.alumno_user.pk,
            nombre="Ana",
            apellido="Lopez",
            curp="LOPA000101MDFXXX01",
            email="alum@example.com",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.docente = Docente.objects.create(
            user_id=self.docente_user.pk,
            nombre="Carlos",
            apellido="Ruiz",
            email="profe@example.com",
        )
        DocenteCurso.objects.create(docente=self.docente, curso=self.curso)
        self.inscripcion = Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso,
            periodo=self.periodo,
        )
        self.http_alum = Client()
        self.http_alum.login(username="alum", password="secret123")
        self.http_profe = Client()
        self.http_profe.login(username="profe", password="secret123")

    def test_alumno_no_crea_actividad(self):
        response = self.http_alum.post(
            reverse("aula_actividad_nueva", args=[self.curso.pk]),
            {
                "nombre": "Tarea 1",
                "fecha_limite": (timezone.localdate() + timedelta(days=3)).isoformat(),
                "valor": "100",
                "tipo": "tarea",
                "estado": "activa",
            },
        )
        self.assertEqual(Actividad.objects.count(), 0)
        self.assertEqual(response.status_code, 403)

    def test_docente_crea_alumno_entrega_y_kardex(self):
        response = self.http_profe.post(
            reverse("aula_actividad_nueva", args=[self.curso.pk]),
            {
                "nombre": "Ensayo",
                "descripcion": "Escribe un ensayo",
                "fecha_limite": (timezone.localdate() + timedelta(days=5)).isoformat(),
                "valor": "100",
                "tipo": "tarea",
                "estado": "activa",
            },
        )
        self.assertRedirects(response, reverse("aula_curso", args=[self.curso.pk]))
        actividad = Actividad.objects.get()
        entregar = self.http_alum.post(
            reverse("aula_entregar", args=[actividad.pk]),
            {"entrega": "Mi ensayo"},
        )
        self.assertRedirects(entregar, reverse("aula_curso", args=[self.curso.pk]))
        registro = CalificacionActividad.objects.get(actividad=actividad, inscripcion=self.inscripcion)
        self.assertTrue(registro.entregado)
        prefix = str(self.inscripcion.pk)
        calificar = self.http_profe.post(
            reverse("aula_guardar_calificacion", args=[actividad.pk, self.inscripcion.pk]),
            {f"{prefix}-calificacion": "80", f"{prefix}-comentarios": "Bien"},
        )
        self.assertRedirects(calificar, reverse("aula_calificar", args=[actividad.pk]))
        self.inscripcion.refresh_from_db()
        self.assertEqual(self.inscripcion.calificacion, Decimal("80.00"))
        kardex = self.http_alum.get(reverse("sii_kardex"))
        self.assertContains(kardex, "80")
        redirect = self.http_alum.get(reverse("aula_kardex"))
        self.assertRedirects(redirect, reverse("sii_kardex"))

    def test_sidebar_aula_ya_no_lista_kardex(self):
        response = self.http_alum.get(reverse("aula_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Kardex")

    def test_pendiente_de_pago_bloquea_entrega(self):
        self.inscripcion.puede_cursar = False
        self.inscripcion.save(update_fields=["puede_cursar"])
        actividad = Actividad.objects.create(
            curso=self.curso, nombre="Tarea paga", fecha_limite=date.today(), valor=Decimal("10")
        )
        response = self.http_alum.post(
            reverse("aula_entregar", args=[actividad.pk]),
            {"entrega": "No debería entrar"},
        )
        self.assertRedirects(response, reverse("aula_curso", args=[self.curso.pk]))
        self.assertFalse(CalificacionActividad.objects.filter(actividad=actividad, entregado=True).exists())

    def test_alumno_no_entra_a_calificar(self):
        actividad = Actividad.objects.create(
            curso=self.curso, nombre="Quiz", fecha_limite=date.today(), valor=Decimal("10")
        )
        response = self.http_alum.get(reverse("aula_calificar", args=[actividad.pk]))
        self.assertEqual(response.status_code, 403)

    def test_actualizar_kardex_ponderado(self):
        a1 = Actividad.objects.create(
            curso=self.curso, nombre="A", fecha_limite=date.today(), valor=Decimal("50")
        )
        a2 = Actividad.objects.create(
            curso=self.curso, nombre="B", fecha_limite=date.today(), valor=Decimal("50")
        )
        CalificacionActividad.objects.create(
            actividad=a1, inscripcion=self.inscripcion, calificacion=Decimal("50")
        )
        CalificacionActividad.objects.create(
            actividad=a2, inscripcion=self.inscripcion, calificacion=Decimal("40")
        )
        promedio = actualizar_kardex(self.inscripcion)
        self.assertEqual(promedio, Decimal("90.00"))
