from datetime import date

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from campus.models import CampusPreferencia
from sii.models import Alumno
from sii.permissions import GRUPO_ALUMNO, crear_grupos


class CampusAparienciaTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("pref1", "pref1@example.com", "secret123")
        self.otro = User.objects.create_user("pref2", "pref2@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Ana",
            apellido="Pref",
            email="pref1@example.com",
            curp="PRAN000101MDFXXX11",
            fecha_nacimiento=date(2000, 1, 1),
        )
        Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Beto",
            apellido="Pref",
            email="pref2@example.com",
            curp="PRBE000101HDFXXX11",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)

    def test_configuracion_persiste_tema_y_acento(self):
        pagina = self.http.get(reverse("campus_configuracion"))
        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, "Tema")
        self.assertContains(pagina, "Rojo Ingenio")
        self.assertContains(pagina, 'data-campus-tema="claro"')
        self.http.post(
            reverse("campus_configuracion"),
            {"tema": "oscuro", "acento": "vino", "animacion_carga": "on"},
        )
        pref = CampusPreferencia.objects.get(user_id=self.user.pk)
        self.assertEqual(pref.tema, "oscuro")
        self.assertEqual(pref.acento, "vino")
        self.assertTrue(pref.animacion_carga)
        inicio = self.http.get(reverse("campus_inicio"))
        self.assertContains(inicio, 'data-campus-tema="oscuro"')
        self.assertContains(inicio, 'data-campus-acento="vino"')
        self.assertContains(inicio, "campus-tema-oscuro")

    def test_no_altera_preferencias_de_otro(self):
        CampusPreferencia.objects.create(user_id=self.otro.pk, tema="oscuro", acento="carbon")
        self.http.post(
            reverse("campus_configuracion"),
            {"tema": "claro", "acento": "arena"},
        )
        ajeno = CampusPreferencia.objects.get(user_id=self.otro.pk)
        self.assertEqual(ajeno.tema, "oscuro")
        self.assertEqual(ajeno.acento, "carbon")
        propio = CampusPreferencia.objects.get(user_id=self.user.pk)
        self.assertEqual(propio.acento, "arena")

    def test_animacion_se_puede_apagar(self):
        self.http.post(
            reverse("campus_configuracion"),
            {"tema": "claro", "acento": "rojo"},
        )
        pref = CampusPreferencia.objects.get(user_id=self.user.pk)
        self.assertFalse(pref.animacion_carga)
        pagina = self.http.get(reverse("campus_configuracion"))
        self.assertContains(pagina, 'data-campus-carga="0"')
        self.assertContains(pagina, "indicador simple")
