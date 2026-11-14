from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from aula.models import Actividad, CalificacionActividad, Recurso, SeccionTema
from campus.services.ludico import perfil_de
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ALUMNO, crear_grupos
from ventas.models import EdicionCurso, Producto


class CampusSeccionesRetoTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("sec1", "sec1@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Sel",
            apellido="Unidad",
            email="sec1@example.com",
            curp="UNSE000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        hoy = timezone.localdate()
        self.periodo = Periodo.objects.create(
            nombre="Sec", fecha_inicio=hoy.replace(day=1), fecha_fin=hoy.replace(year=hoy.year + 1)
        )
        self.curso = Curso.objects.create(nombre="Unidades")
        producto = Producto.objects.create(producto="Unidades", precio_unitario=Decimal("10"), id_curso=self.curso)
        self.edicion = EdicionCurso.objects.create(
            id_curso=producto,
            codigo_edicion="UNI-A",
            fecha_inicio=self.periodo.fecha_inicio,
            fecha_fin=self.periodo.fecha_fin,
        )
        self.ins = Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso,
            periodo=self.periodo,
            estado="activo",
            id_edicion=self.edicion,
        )
        self.s1 = SeccionTema.objects.create(curso=self.curso, edicion=self.edicion, titulo="Unidad 1", orden=1)
        self.s2 = SeccionTema.objects.create(curso=self.curso, edicion=self.edicion, titulo="Unidad 2", orden=2)
        Recurso.objects.create(seccion=self.s2, titulo="PDF 2", tipo=Recurso.TIPO_TEXTO, cuerpo="material dos")
        self.a1 = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            seccion=self.s1,
            nombre="Tarea 1",
            fecha_limite=hoy + timedelta(days=5),
            valor=Decimal("10"),
        )
        self.a2 = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            seccion=self.s2,
            nombre="Tarea 2",
            fecha_limite=hoy + timedelta(days=5),
            valor=Decimal("10"),
        )
        self.http = Client()
        self.http.force_login(self.user)

    def test_candado_ludico_no_impide_entrega_ni_material(self):
        grupo = reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk])
        pagina = self.http.get(grupo)
        self.assertContains(pagina, "Reto de la unidad bloqueado")
        self.assertContains(pagina, "material dos")
        self.assertNotContains(pagina, "candado académico")
        entrega = self.http.post(reverse("aula_entregar", args=[self.a2.pk]), {"entrega": "aunque el reto esté cerrado"})
        self.assertRedirects(entrega, grupo)
        self.assertTrue(CalificacionActividad.objects.filter(actividad=self.a2, entregado=True).exists())
        self.http.post(reverse("aula_entregar", args=[self.a1.pk]), {"entrega": "unidad 1"})
        self.assertGreaterEqual(perfil_de(self.alumno).xp, 15)
        abierta = self.http.get(grupo)
        self.assertNotContains(abierta, "Reto de la unidad bloqueado")

    def test_candado_academico_si_oculta(self):
        self.edicion.candado_academico = True
        self.edicion.save(update_fields=["candado_academico"])
        grupo = reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk])
        pagina = self.http.get(grupo)
        self.assertContains(pagina, "candado académico")
        self.assertNotContains(pagina, "material dos")
        entrega = self.http.post(reverse("aula_entregar", args=[self.a2.pk]), {"entrega": "no"})
        self.assertRedirects(entrega, grupo)
        self.assertFalse(CalificacionActividad.objects.filter(actividad=self.a2, entregado=True).exists())
