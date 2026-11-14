from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from sii.identity import destino_post_login
from sii.models import Alumno, Curso, Inscripcion, Periodo
from sii.permissions import GRUPO_ALUMNO, GRUPO_VENDEDOR, crear_grupos
from aula.models import Actividad, AvisoGrupo, CalificacionActividad
from campus.models import AvisoInstitucional, AvisoLectura
from campus.services.calendario import hitos_calendario
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
        self.assertContains(response, reverse("campus_ficha"))
        self.assertContains(response, reverse("usuario"))
        self.assertContains(response, reverse("logout"))
        self.assertContains(response, "Cerrar sesión")
        self.assertContains(response, 'aria-label="Perfil"')
        self.assertNotContains(response, self.alumno.curp)
        self.assertNotContains(response, "5512345678")
        self.assertEqual(self.http.get(reverse("logout")).status_code, 302)


class CampusCalendarioTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("alum6", "alum6@example.com", "secret123")
        self.otro = User.objects.create_user("alum6b", "alum6b@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Cal",
            apellido="Endario",
            email="alum6@example.com",
            curp="ENCA000101MDFXXX06",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.ajeno = Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otro",
            apellido="Cal",
            email="alum6b@example.com",
            curp="OTCA000101HDFXXX06",
            fecha_nacimiento=date(2000, 1, 1),
        )
        hoy = date.today()
        self.periodo = Periodo.objects.create(
            nombre="Actual",
            fecha_inicio=hoy.replace(day=1),
            fecha_fin=hoy.replace(year=hoy.year + 1),
            fecha_publicacion_calificaciones=hoy.replace(year=hoy.year + 1),
        )
        self.siguiente = Periodo.objects.create(
            nombre="Siguiente",
            fecha_inicio=date(self.periodo.fecha_fin.year + 1, 1, 15),
            fecha_fin=date(self.periodo.fecha_fin.year + 1, 6, 30),
        )
        self.curso = Curso.objects.create(nombre="Cálculo")
        self.curso_ajeno = Curso.objects.create(nombre="Ajeno")
        self.ins = Inscripcion.objects.create(
            alumno=self.alumno, curso=self.curso, periodo=self.periodo, estado="activo"
        )
        Inscripcion.objects.create(
            alumno=self.ajeno, curso=self.curso_ajeno, periodo=self.periodo, estado="activo"
        )
        self.propia = Actividad.objects.create(
            curso=self.curso, nombre="Tarea mía", fecha_limite=date.today(), valor=Decimal("10")
        )
        self.ajena = Actividad.objects.create(
            curso=self.curso_ajeno, nombre="Tarea ajena", fecha_limite=date.today(), valor=Decimal("10")
        )
        self.http = Client()
        self.http.force_login(self.user)

    def test_hitos_y_filtro_de_grupo(self):
        response = self.http.get(reverse("campus_calendario"))
        self.assertContains(response, "Inicio del periodo")
        self.assertContains(response, "Fin del periodo")
        self.assertContains(response, "Publicación de calificaciones")
        self.assertContains(response, "Próximo periodo: Siguiente")
        self.assertContains(response, "Tarea mía")
        self.assertContains(response, reverse("aula_entregar", args=[self.propia.pk]))
        self.assertNotContains(response, "Tarea ajena")
        titulos = [h["titulo"] for h in hitos_calendario(self.alumno)["hitos"]]
        self.assertTrue(any("Tarea mía" in t for t in titulos))
        self.assertFalse(any("Tarea ajena" in t for t in titulos))

    def test_vacio_sin_inscripcion(self):
        self.ins.delete()
        response = self.http.get(reverse("campus_calendario"))
        self.assertContains(response, "No hay un periodo ni inscripciones")
        self.assertNotContains(response, "Inicio del periodo")


class CampusFichaTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("alum7", "alum7@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Nora",
            apellido="Gil",
            email="alum7@example.com",
            curp="GINO000101MDFXXX07",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.http = Client()
        self.http.force_login(self.user)

    def test_guarda_contacto_y_no_curp(self):
        response = self.http.post(
            reverse("campus_ficha"),
            {
                "telefono": "5511223344",
                "email_personal": "nora.personal@example.com",
                "direccion_calle": "Calle 10",
                "colonia": "Centro",
                "codigo_postal": "01000",
                "ciudad": "CDMX",
                "estado_domicilio": "Ciudad de México",
                "empresa": "ACME",
                "puesto": "Becaria",
                "telefono_laboral": "",
                "contacto_emergencia_nombre": "Luis",
                "contacto_emergencia_telefono": "5599887766",
            },
        )
        self.assertRedirects(response, reverse("campus_ficha"))
        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.telefono, "5511223344")
        self.assertEqual(self.alumno.codigo_postal, "01000")
        self.assertEqual(self.alumno.curp, "GINO000101MDFXXX07")
        self.assertEqual(self.alumno.email, "alum7@example.com")
        self.assertEqual(self.alumno.nombre, "Nora")

    def test_cp_invalido(self):
        response = self.http.post(
            reverse("campus_ficha"),
            {"telefono": "5511223344", "codigo_postal": "abc", "email_personal": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5 dígitos")

    def test_solo_lectura_en_plantilla(self):
        response = self.http.get(reverse("campus_ficha"))
        self.assertContains(response, "solo lectura")
        self.assertContains(response, self.alumno.curp)
        self.assertNotContains(response, 'name="curp"')
        self.assertNotContains(response, 'name="nombre"')

    def test_vendedor_no_edita_ficha_campus(self):
        vend = User.objects.create_user("vend7", "vend7@example.com", "secret123")
        vend.groups.add(Group.objects.get(name=GRUPO_VENDEDOR))
        http = Client()
        http.force_login(vend)
        self.assertEqual(http.get(reverse("campus_ficha")).status_code, 403)


class CampusAvisosTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.user = User.objects.create_user("alum8", "alum8@example.com", "secret123")
        self.otro = User.objects.create_user("alum8b", "alum8b@example.com", "secret123")
        self.user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.otro.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.alumno = Alumno.objects.create(
            user_id=self.user.pk,
            nombre="Avi",
            apellido="So",
            email="alum8@example.com",
            curp="SOAV000101MDFXXX08",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.ajeno = Alumno.objects.create(
            user_id=self.otro.pk,
            nombre="Otro",
            apellido="Avi",
            email="alum8b@example.com",
            curp="OTAV000101HDFXXX08",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.aviso = AvisoInstitucional.objects.create(
            titulo="Cierre de caja",
            cuerpo="Revisa tu saldo",
            tipo=AvisoInstitucional.TIPO_IMPORTANTE,
            publicado=True,
        )
        self.borrador = AvisoInstitucional.objects.create(
            titulo="Borrador oculto",
            cuerpo="No",
            publicado=False,
        )
        self.http = Client()
        self.http.force_login(self.user)
        self.http_otro = Client()
        self.http_otro.force_login(self.otro)

    def test_publicado_vs_borrador(self):
        response = self.http.get(reverse("campus_avisos"))
        self.assertContains(response, "Cierre de caja")
        self.assertNotContains(response, "Borrador oculto")
        inicio = self.http.get(reverse("campus_inicio"))
        self.assertContains(inicio, "Aviso importante")

    def test_marcar_leido_no_afecta_a_otro(self):
        leer = self.http.post(reverse("campus_aviso_leer", args=[self.aviso.pk]))
        self.assertRedirects(leer, reverse("campus_avisos"))
        self.assertTrue(AvisoLectura.objects.filter(aviso=self.aviso, alumno=self.alumno).exists())
        self.assertFalse(AvisoLectura.objects.filter(aviso=self.aviso, alumno=self.ajeno).exists())
        propio = self.http.get(reverse("campus_avisos") + "?estado=leidos")
        self.assertContains(propio, "Cierre de caja")
        ajeno = self.http_otro.get(reverse("campus_avisos") + "?estado=leidos")
        self.assertNotContains(ajeno, "Cierre de caja")
        inicio = self.http.get(reverse("campus_inicio"))
        self.assertNotContains(inicio, "Aviso importante: Cierre de caja")

    def test_aviso_de_grupo_agregado(self):
        periodo = Periodo.objects.create(
            nombre="A", fecha_inicio=date.today(), fecha_fin=date.today().replace(year=date.today().year + 1)
        )
        curso = Curso.objects.create(nombre="Grupo")
        Inscripcion.objects.create(alumno=self.alumno, curso=curso, periodo=periodo, estado="activo")
        AvisoGrupo.objects.create(curso=curso, titulo="Aviso del grupo", cuerpo="Hola", publicado=True)
        response = self.http.get(reverse("campus_avisos"))
        self.assertContains(response, "Aviso del grupo")
        self.assertContains(response, "Tu grupo")
