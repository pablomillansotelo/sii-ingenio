from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from aula.models import Actividad, CalificacionActividad
from campus.models import AvisoInstitucional, Notificacion
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ALUMNO, crear_grupos


class CampusNotificacionesTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("not1", "not1@example.com", "secret123")
        self.otro = User.objects.create_user("not2", "not2@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Nia",
            apellido="Nota",
            email="not1@example.com",
            curp="NONI000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otra",
            apellido="Nota",
            email="not2@example.com",
            curp="NOOT000101HDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        hoy = date.today()
        self.periodo = Periodo.objects.create(
            nombre="Notif", fecha_inicio=hoy.replace(day=1), fecha_fin=hoy.replace(year=hoy.year + 1)
        )
        self.curso = Curso.objects.create(nombre="Ética")
        self.ins = Inscripcion.objects.create(
            alumno=self.alumno, curso=self.curso, periodo=self.periodo, estado="activo"
        )
        self.act = Actividad.objects.create(
            curso=self.curso,
            nombre="Ensayo",
            fecha_limite=hoy + timedelta(days=2),
            valor=Decimal("10"),
        )
        CalificacionActividad.objects.create(
            actividad=self.act, inscripcion=self.ins, calificacion=Decimal("9.00"), entregado=True
        )
        AvisoInstitucional.objects.create(
            titulo="Aviso clave",
            cuerpo="Lee esto",
            tipo=AvisoInstitucional.TIPO_IMPORTANTE,
            publicado=True,
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)

    def test_propias_sin_duplicar(self):
        primera = self.http.get(reverse("campus_notificaciones"))
        self.assertContains(primera, "Ensayo")
        self.assertContains(primera, "Por vencer")
        self.assertContains(primera, "Calificación")
        self.assertContains(primera, "Aviso clave")
        self.assertContains(primera, reverse("campus_kardex"))
        n = Notificacion.objects.filter(user_id=self.user.pk).count()
        self.http.get(reverse("campus_notificaciones"))
        self.assertEqual(Notificacion.objects.filter(user_id=self.user.pk).count(), n)
        ajena = self.http_otro.get(reverse("campus_notificaciones"))
        self.assertNotContains(ajena, "Ensayo")
        self.assertFalse(Notificacion.objects.filter(user_id=self.otro.pk, titulo__icontains="Ensayo").exists())
        item = Notificacion.objects.filter(user_id=self.user.pk).first()
        self.http.post(reverse("campus_notificacion_leer", args=[item.pk]))
        item.refresh_from_db()
        self.assertIsNotNone(item.leida_en)
        self.http.post(reverse("campus_notificaciones_leer_todas"))
        self.assertFalse(
            Notificacion.objects.filter(user_id=self.user.pk, leida_en__isnull=True).exists()
        )
