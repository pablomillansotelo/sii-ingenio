from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from sii.identity import destino_post_login
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ALUMNO, GRUPO_VENDEDOR, crear_grupos
from aula.models import Actividad, CalificacionActividad
from campus.services.cursos import tarjetas_curso_actual
from campus.services.identidad import identidad_campus, iniciales_de
from sii.services.avance import avance_academico
from ventas.models import EdicionCurso, Producto, Vendedor


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


class CampusAvanceTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("alum2", "alum2@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Eva",
            apellido="Ruiz",
            email="alum2@example.com",
            curp="RUEV000101MDFXXX08",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.periodo = Periodo.objects.create(
            nombre="2026-A", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 6, 30)
        )
        self.curso_a = Curso.objects.create(nombre="Álgebra")
        self.curso_b = Curso.objects.create(nombre="Historia")
        self.http = Client()
        self.http.force_login(self.user)

    def test_sin_inscripciones_estado_vacio(self):
        data = avance_academico(self.alumno)
        self.assertFalse(data["tiene_inscripciones"])
        response = self.http.get(reverse("campus_inicio"))
        self.assertContains(response, "Aún no tienes inscripciones")
        self.assertContains(response, "Ver kardex")

    def test_promedio_ignora_en_curso_y_baja(self):
        Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso_a,
            periodo=self.periodo,
            calificacion=Decimal("8.00"),
            estado="completado",
        )
        Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso_b,
            periodo=self.periodo,
            calificacion=None,
            estado="activo",
        )
        data = avance_academico(self.alumno)
        self.assertEqual(data["promedio"], Decimal("8.00"))
        self.assertEqual(data["materias_x"], 1)
        self.assertEqual(data["materias_y"], 2)
        self.assertEqual(data["porcentaje"], 50)

        baja_curso = Curso.objects.create(nombre="Baja")
        Inscripcion.objects.create(
            alumno=self.alumno,
            curso=baja_curso,
            periodo=self.periodo,
            calificacion=Decimal("9.00"),
            estado="cancelado",
        )
        data = avance_academico(self.alumno)
        self.assertEqual(data["promedio"], Decimal("8.00"))
        self.assertEqual(data["materias_x"], 1)
        self.assertEqual(data["materias_y"], 3)
        response = self.http.get(reverse("campus_inicio"))
        self.assertContains(response, "8.00")
        self.assertContains(response, "1 de 3")
        self.assertContains(response, reverse("sii_kardex"))
        self.assertContains(response, "Sin plan de estudios formal")


class CampusCursoActualTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("alum3", "alum3@example.com", "secret123")
        self.otro = User.objects.create_user("alum4", "alum4@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Lia",
            apellido="Sol",
            email="alum3@example.com",
            curp="SOLI000101MDFXXX01",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.ajeno = Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otro",
            apellido="Alum",
            email="alum4@example.com",
            curp="OTRO000101HDFXXX02",
            fecha_nacimiento=date(2000, 1, 1),
        )
        hoy = date.today()
        self.periodo = Periodo.objects.create(
            nombre="Vigente", fecha_inicio=hoy.replace(day=1), fecha_fin=hoy.replace(year=hoy.year + 1)
        )
        self.curso = Curso.objects.create(nombre="Diseño")
        self.curso_b = Curso.objects.create(nombre="Foto")
        self.producto = Producto.objects.create(
            producto="Diseño", precio_unitario=Decimal("1000"), id_curso=self.curso
        )
        self.edicion = EdicionCurso.objects.create(
            id_curso=self.producto,
            codigo_edicion="DIS-A",
            fecha_inicio=self.periodo.fecha_inicio,
            fecha_fin=self.periodo.fecha_fin,
        )
        self.ins = Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso,
            periodo=self.periodo,
            id_edicion=self.edicion,
            estado="activo",
            puede_cursar=True,
        )
        self.http = Client()
        self.http.force_login(self.user)

    def test_varias_tarjetas_y_cta_al_aula(self):
        Inscripcion.objects.create(
            alumno=self.alumno, curso=self.curso_b, periodo=self.periodo, estado="activo"
        )
        response = self.http.get(reverse("campus_inicio"))
        self.assertContains(response, "Diseño")
        self.assertContains(response, "Foto")
        self.assertContains(response, "Ir al curso")
        self.assertContains(response, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertContains(response, reverse("aula_curso", args=[self.curso_b.pk]))

    def test_baja_no_aparece(self):
        self.ins.estado = "cancelado"
        self.ins.save(update_fields=["estado"])
        data = tarjetas_curso_actual(self.alumno)
        self.assertEqual(data["tarjetas"], [])
        response = self.http.get(reverse("campus_inicio"))
        self.assertContains(response, "No tienes cursos en este periodo")

    def test_gate_de_pago_sin_saltar_aula(self):
        self.ins.puede_cursar = False
        self.ins.save(update_fields=["puede_cursar"])
        response = self.http.get(reverse("campus_inicio"))
        self.assertContains(response, "Diseño")
        self.assertContains(response, "pago pendiente")
        self.assertNotContains(response, "Ir al curso")

    def test_progreso_por_entregas(self):
        act = Actividad.objects.create(
            curso=self.curso, edicion=self.edicion, nombre="Tarea", fecha_limite=date.today(), valor=Decimal("10")
        )
        Actividad.objects.create(
            curso=self.curso, edicion=self.edicion, nombre="Examen", fecha_limite=date.today(), valor=Decimal("10")
        )
        CalificacionActividad.objects.create(
            actividad=act, inscripcion=self.ins, entregado=True, entrega="ok"
        )
        tarjeta = tarjetas_curso_actual(self.alumno)["tarjetas"][0]
        self.assertEqual(tarjeta["progreso"]["hechos"], 1)
        self.assertEqual(tarjeta["progreso"]["total"], 2)

    def test_no_lista_cursos_de_otro(self):
        Inscripcion.objects.create(
            alumno=self.ajeno, curso=self.curso_b, periodo=self.periodo, estado="activo"
        )
        nombres = [t["curso"].nombre for t in tarjetas_curso_actual(self.alumno)["tarjetas"]]
        self.assertEqual(nombres, ["Diseño"])


class CampusPerfilTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("alum5", "cuenta5@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Mario",
            apellido="Nava",
            email="expediente5@example.com",
            telefono="5512345678",
            curp="NAMA000101HDFXXX03",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.http = Client()
        self.http.force_login(self.user)

    def test_iniciales_e_identidad(self):
        self.assertEqual(iniciales_de("Mario Nava"), "MN")
        data = identidad_campus(self.user, self.alumno)
        self.assertEqual(data["iniciales"], "MN")
        self.assertEqual(data["identificador_etiqueta"], "Código Ingenio")
        self.assertTrue(data["identificador"].startswith("ING-"))
        labels = [c["label"] for c in data["correos"]]
        self.assertIn("Correo del expediente", labels)
        self.assertIn("Correo de la cuenta", labels)

    def test_menu_perfil_y_logout(self):
        response = self.http.get(reverse("campus_inicio"))
        self.assertContains(response, "MN")
        self.assertContains(response, "Mario Nava")
        self.assertContains(response, "Código Ingenio")
        self.assertContains(response, reverse("sii_mi_ficha"))
        self.assertContains(response, reverse("usuario"))
        self.assertContains(response, reverse("logout"))
        self.assertContains(response, "Cerrar sesión")
        self.assertContains(response, 'aria-label="Perfil"')
        self.assertNotContains(response, self.alumno.curp)
        self.assertNotContains(response, "5512345678")
        self.assertEqual(self.http.get(reverse("logout")).status_code, 302)
