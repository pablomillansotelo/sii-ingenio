from datetime import date

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from campus.models import Hilo
from sii.models import Alumno, Curso, Docente, DocenteCurso, Inscripcion, Periodo
from sii.permissions import GRUPO_ADMINISTRADOR, GRUPO_ALUMNO, GRUPO_DOCENTE, crear_grupos


class CampusMensajesTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("msg1", "msg1@example.com", "secret123")
        self.otro = User.objects.create_user("msg2", "msg2@example.com", "secret123")
        self.admin = User.objects.create_user("msgadm", "msgadm@example.com", "secret123")
        self.profe = User.objects.create_user("msgprofe", "msgprofe@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMINISTRADOR))
        self.profe.groups.add(Group.objects.get(name=GRUPO_DOCENTE))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Mia",
            apellido="Mail",
            email="msg1@example.com",
            curp="MAMI000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otra",
            apellido="Mail",
            email="msg2@example.com",
            curp="MAOT000101HDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.docente = Docente.objects.create(
            user_id=self.profe.pk,
            nombre="Paz",
            apellido="Profe",
            email="msgprofe@example.com",
        )
        hoy = date.today()
        self.periodo = Periodo.objects.create(
            nombre="Msg", fecha_inicio=hoy.replace(day=1), fecha_fin=hoy.replace(year=hoy.year + 1)
        )
        self.curso = Curso.objects.create(nombre="Dibujo")
        Inscripcion.objects.create(
            alumno=self.alumno, curso=self.curso, periodo=self.periodo, estado="activo"
        )
        DocenteCurso.objects.create(docente=self.docente, curso=self.curso)
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)
        self.http_admin = Client()
        self.http_admin.force_login(self.admin)
        self.http_profe = Client()
        self.http_profe.force_login(self.profe)

    def test_hilo_con_control_y_aislamiento(self):
        pagina = self.http.get(reverse("campus_mensajes"))
        self.assertContains(pagina, "Bandeja de mensajes")
        self.assertContains(pagina, "Control escolar")
        self.assertContains(pagina, "Docente Paz")
        self.http.post(
            reverse("campus_mensajes"),
            {"destino": "control", "asunto": "Beca", "cuerpo": "¿Hay convocatoria?"},
        )
        hilo = Hilo.objects.get()
        self.assertTrue(hilo.para_control)
        staff = self.http_admin.get(reverse("sii_hilo", args=[hilo.pk]))
        self.assertContains(staff, "¿Hay convocatoria?")
        self.http_admin.post(reverse("sii_hilo", args=[hilo.pk]), {"cuerpo": "Sí, en avisos."})
        alumno_ve = self.http.get(reverse("campus_hilo", args=[hilo.pk]))
        self.assertContains(alumno_ve, "Sí, en avisos.")
        ajeno = self.http_otro.get(reverse("campus_hilo", args=[hilo.pk]))
        self.assertIn(ajeno.status_code, (403, 404))
        entre_alumnos = self.http.post(
            reverse("campus_mensajes"),
            {"destino": f"alumno:{self.otro.pk}", "asunto": "Hola", "cuerpo": "no debe"},
        )
        self.assertContains(entre_alumnos, "Solo staff")
        self.assertEqual(Hilo.objects.count(), 1)

    def test_hilo_con_docente_del_grupo(self):
        self.http.post(
            reverse("campus_mensajes"),
            {"destino": f"docente:{self.profe.pk}", "asunto": "Tarea", "cuerpo": "¿Hasta cuándo?"},
        )
        hilo = Hilo.objects.get()
        self.assertFalse(hilo.para_control)
        profe = self.http_profe.get(reverse("sii_hilo", args=[hilo.pk]))
        self.assertContains(profe, "¿Hasta cuándo?")
        inicio = self.http_profe.get(reverse("campus_inicio"))
        self.assertEqual(inicio.status_code, 403)
