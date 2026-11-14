from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from campus.services.ludico import acreditar, nivel_de, perfil_de
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ADMINISTRADOR, GRUPO_ALUMNO, crear_grupos
from ventas.models import Cliente, Producto, Venta, VentaDetalle, Vendedor


class CampusLudicoTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("lud1", "lud1@example.com", "secret123")
        self.otro = User.objects.create_user("lud2", "lud2@example.com", "secret123")
        self.admin = User.objects.create_user("ludadm", "ludadm@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMINISTRADOR))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Lua",
            apellido="Dico",
            email="lud1@example.com",
            curp="DILU000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.ajeno = Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otra",
            apellido="Dico",
            email="lud2@example.com",
            curp="DIOT000101HDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        hoy = date.today()
        self.periodo = Periodo.objects.create(
            nombre="Lud", fecha_inicio=hoy.replace(day=1), fecha_fin=hoy.replace(year=hoy.year + 1)
        )
        self.curso = Curso.objects.create(nombre="Ludica")
        self.ins = Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso,
            periodo=self.periodo,
            estado="completado",
            calificacion=Decimal("8.50"),
        )
        self.vend_user = User.objects.create_user("ludvend", "ludvend@example.com", "secret123")
        vendedor = Vendedor.objects.create(user_id=self.vend_user.pk, nombre="Vend", email="ludvend@example.com")
        cliente = Cliente.objects.create(
            nombre="Lua", apellidos="Dico", direccion="Calle", email="lud1@example.com"
        )
        producto = Producto.objects.create(producto="Ludica", precio_unitario=Decimal("500"), id_curso=self.curso)
        self.venta = Venta.objects.create(
            id_cliente=cliente,
            id_vendedor=vendedor,
            estado=Venta.ESTADO_CONFIRMADA,
        )
        VentaDetalle.objects.create(
            id_venta=self.venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("500")
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)
        self.http_admin = Client()
        self.http_admin.force_login(self.admin)

    def test_nivel_monedas_y_aislamiento(self):
        self.assertEqual(nivel_de(0), 1)
        self.assertEqual(nivel_de(99), 1)
        self.assertEqual(nivel_de(100), 2)
        perfil = acreditar(self.alumno, 250, "Prueba", "prueba-1")
        self.assertEqual(perfil.xp, 250)
        self.assertEqual(perfil.nivel, 3)
        self.assertEqual(perfil.monedas, 25)
        acreditar(self.alumno, 250, "Prueba", "prueba-1")
        perfil.refresh_from_db()
        self.assertEqual(perfil.xp, 250)
        self.ins.refresh_from_db()
        self.assertEqual(self.ins.calificacion, Decimal("8.50"))
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.monto, Decimal("500"))
        inicio = self.http.get(reverse("campus_inicio"))
        self.assertContains(inicio, "Nivel 3")
        self.assertContains(inicio, "no afecta kardex")
        pagina = self.http.get(reverse("campus_ludico"))
        self.assertContains(pagina, "No son calificación")
        self.assertContains(pagina, "Nadie ha activado")
        ajeno = self.http_otro.get(reverse("campus_ludico"))
        self.assertNotContains(ajeno, "250 XP")
        self.assertEqual(perfil_de(self.ajeno).xp, 0)
        self.http.post(reverse("campus_ludico"), {"ranking_publico": "on"})
        ranking = self.http.get(reverse("campus_ludico"))
        self.assertContains(ranking, "Lua")
        self.http_admin.post(reverse("sii_ludico_reset", args=[self.alumno.pk]))
        perfil.refresh_from_db()
        self.assertEqual(perfil.xp, 0)
        self.assertEqual(perfil.reset_por_id, self.admin.pk)
        self.ins.refresh_from_db()
        self.assertEqual(self.ins.calificacion, Decimal("8.50"))
