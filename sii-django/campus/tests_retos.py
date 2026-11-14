from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from aula.models import Actividad, CalificacionActividad
from campus.models import MovimientoXP, RetoSemanal
from campus.services.ludico import perfil_de
from campus.services.retos import lunes_semana, sincronizar_retos
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ALUMNO, crear_grupos


class CampusRetosTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("reto1", "reto1@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Rene",
            apellido="Reto",
            email="reto1@example.com",
            curp="RERE000101HDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        hoy = date.today()
        self.periodo = Periodo.objects.create(
            nombre="Retos", fecha_inicio=hoy.replace(day=1), fecha_fin=hoy.replace(year=hoy.year + 1)
        )
        self.curso = Curso.objects.create(nombre="Semanal")
        self.ins = Inscripcion.objects.create(
            alumno=self.alumno, curso=self.curso, periodo=self.periodo, estado="activo"
        )
        self.act = Actividad.objects.create(
            curso=self.curso, nombre="Quiz", fecha_limite=hoy + timedelta(days=3), valor=Decimal("10")
        )
        self.http = Client()
        self.http.force_login(self.user)

    def test_progreso_y_premio_unico(self):
        self.assertEqual(lunes_semana().weekday(), 0)
        inicio = self.http.get(reverse("campus_inicio"))
        self.assertContains(inicio, "Retos de la semana")
        self.assertContains(inicio, "0 de 1")
        reto = RetoSemanal.objects.get(inscripcion=self.ins)
        self.assertEqual(reto.progreso, 0)
        CalificacionActividad.objects.create(
            actividad=self.act,
            inscripcion=self.ins,
            entregado=True,
            fecha_entrega=timezone.localdate(),
        )
        sincronizar_retos(self.alumno)
        sincronizar_retos(self.alumno)
        reto.refresh_from_db()
        self.assertEqual(reto.progreso, 1)
        self.assertIsNotNone(reto.completado_en)
        self.assertEqual(
            MovimientoXP.objects.filter(perfil=perfil_de(self.alumno), clave__startswith="reto-sem-").count(),
            1,
        )
        self.assertEqual(perfil_de(self.alumno).xp, 20)
        pagina = self.http.get(reverse("campus_inicio"))
        self.assertContains(pagina, "Completado")
