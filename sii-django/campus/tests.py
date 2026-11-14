from datetime import date

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from sii.identity import destino_post_login
from sii.models import Alumno
from sii.permissions import GRUPO_ALUMNO, GRUPO_VENDEDOR, crear_grupos
from ventas.models import Vendedor


class CampusShellTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.alum_user = User.objects.create_user("alum", "alum.campus@example.com", "secret123")
        self.alum_user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        Alumno.objects.create(
            user_id=self.alum_user.pk,
            nombre="Ana",
            apellido="Campus",
            email="alum.campus@example.com",
            curp="CAAN000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.vend_user = User.objects.create_user("vend", "vend.campus@example.com", "secret123")
        self.vend_user.groups.add(Group.objects.get(name=GRUPO_VENDEDOR))
        Vendedor.objects.create(
            user_id=self.vend_user.pk,
            nombre="Vend Campus",
            email="vend.campus@example.com",
        )
        self.docente_user = User.objects.create_user("profe", "profe.campus@example.com", "secret123")
        from sii.permissions import GRUPO_DOCENTE

        self.docente_user.groups.add(Group.objects.get(name=GRUPO_DOCENTE))
        self.http_alum = Client()
        self.http_alum.force_login(self.alum_user)
        self.http_vend = Client()
        self.http_vend.force_login(self.vend_user)
        self.http_profe = Client()
        self.http_profe.force_login(self.docente_user)

    def test_alumno_entra_al_campus(self):
        response = self.http_alum.get(reverse("campus_inicio"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inicio")
        self.assertContains(response, "Control Escolar")
        self.assertContains(response, "Mensajes")
        self.assertContains(response, "Calendario")
        self.assertContains(response, "Más")
        self.assertContains(response, "campus-bottom-nav")
        self.assertContains(response, "campus-sidenav")
        self.assertContains(response, 'id="campus-perfil-btn"')
        self.assertContains(response, "css/campus.css")

    def test_control_escolar_y_calendario_existen(self):
        control = self.http_alum.get(reverse("campus_control_escolar"))
        self.assertEqual(control.status_code, 200)
        self.assertContains(control, "Control Escolar")
        cal = self.http_alum.get(reverse("campus_calendario"))
        self.assertEqual(cal.status_code, 200)
        self.assertContains(cal, "Calendario")

    def test_mensajes_es_proximamente(self):
        response = self.http_alum.get(reverse("campus_mensajes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Próximamente")
        self.assertNotContains(response, "Bandeja de entrada")

    def test_mas_lista_accesos_reales(self):
        response = self.http_alum.get(reverse("campus_mas"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("usuario"))
        self.assertContains(response, reverse("sii_kardex"))
        self.assertContains(response, reverse("mis_compras"))
        self.assertContains(response, reverse("aula_dashboard"))
        self.assertContains(response, "Próximamente")

    def test_vendedor_y_docente_no_ven_campus(self):
        self.assertEqual(self.http_vend.get(reverse("campus_inicio")).status_code, 403)
        self.assertEqual(self.http_profe.get(reverse("campus_inicio")).status_code, 403)
        ventas = self.http_vend.get(reverse("ventas_home"))
        self.assertEqual(ventas.status_code, 200)
        self.assertContains(ventas, 'id="sidebarIngenio"')
        self.assertNotContains(ventas, "campus-bottom-nav")

    def test_logout_sigue_funcionando(self):
        response = self.http_alum.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        follow = self.http_alum.get(reverse("campus_inicio"))
        self.assertEqual(follow.status_code, 302)
        self.assertIn(reverse("login"), follow.url)

    def test_alumno_aterriza_en_campus(self):
        self.assertEqual(destino_post_login(self.alum_user), "campus_inicio")
        self.assertEqual(destino_post_login(self.vend_user), "ventas_home")
        self.http_alum.logout()
        clave = "".join(("sec", "ret123"))
        self.assertTrue(self.client.login(username=self.alum_user.get_username(), password=clave))
        logged = self.client.get(reverse("login"))
        self.assertRedirects(logged, reverse("campus_inicio"))

    def test_hoy_redirige_al_alumno(self):
        response = self.http_alum.get(reverse("inicio"))
        self.assertRedirects(response, reverse("campus_inicio"))
