from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from api.inicio.contextos import contexto_activo, contextos_disponibles
from api.inicio.registro import REGISTRO, registrar, widgets_para
from api.inicio.widgets import Item, Widget, WidgetData
from sii.identity import destino_post_login
from sii.models import Alumno, Curso, Docente, DocenteCurso, Inscripcion, Periodo
from sii.permissions import (
    GRUPO_ADMINISTRADOR,
    GRUPO_ALUMNO,
    GRUPO_DOCENTE,
    GRUPO_VENDEDOR,
    crear_grupos,
)
from ventas.models import Vendedor

QUERY_BUDGET_INICIO = 20


def _limpiar_memo(user):
    for attr in ("_ingenio_roles", "_ingenio_features", "_ingenio_docente", "_inicio_memo"):
        if hasattr(user, attr):
            delattr(user, attr)


def crear_admin(username="admin.inicio"):
    user = User.objects.create_user(username, f"{username}@example.com", "secret123")
    user.groups.add(Group.objects.get(name=GRUPO_ADMINISTRADOR))
    return user


def crear_vendedor(user=None, username="vend.inicio"):
    if user is None:
        user = User.objects.create_user(username, f"{username}@example.com", "secret123")
        user.groups.add(Group.objects.get(name=GRUPO_VENDEDOR))
    Vendedor.objects.create(user_id=user.pk, nombre=username, email=user.email, activo=True)
    _limpiar_memo(user)
    return user


def crear_docente(user=None, cursos=None, username="profe.inicio"):
    if user is None:
        user = User.objects.create_user(username, f"{username}@example.com", "secret123")
        user.groups.add(Group.objects.get(name=GRUPO_DOCENTE))
    docente = Docente.objects.create(
        user_id=user.pk, nombre=username, apellido="Docente", email=user.email
    )
    for curso in cursos or []:
        DocenteCurso.objects.create(docente=docente, curso=curso)
    _limpiar_memo(user)
    return user


def crear_alumno(user=None, username="alum.inicio"):
    if user is None:
        user = User.objects.create_user(username, f"{username}@example.com", "secret123")
        user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
    Alumno.objects.create(
        user_id=user.pk,
        nombre=username,
        apellido="Alumno",
        email=user.email,
        curp=f"A{user.pk:017d}"[:18],
        fecha_nacimiento=date(2000, 1, 1),
    )
    _limpiar_memo(user)
    return user


class InicioFrameworkTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self._backup = {clave: list(widgets) for clave, widgets in REGISTRO.items()}
        self.vend = crear_vendedor()
        self.http = Client()
        self.http.force_login(self.vend)

    def tearDown(self):
        REGISTRO.clear()
        REGISTRO.update({clave: list(widgets) for clave, widgets in self._backup.items()})

    def test_widget_sin_feature_no_aparece(self):
        llamado = {"n": 0}

        def cargar(user, hoy):
            llamado["n"] += 1
            return WidgetData(count=1, items=[Item("X", "y", "/")], cta_url="/", cta_label="Ir")

        registrar(
            Widget(
                clave="test.bajas",
                titulo="Bajas",
                contexto="ventas",
                feature="sii.bajas",
                prioridad=1,
                icono="bi-x",
                cargar=cargar,
            )
        )
        self.assertNotIn("test.bajas", [w.clave for w in widgets_para(self.vend, "ventas")])
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, ">Bajas<")
        self.assertEqual(llamado["n"], 0)

    def test_widget_vacio_y_recorte_de_items(self):
        def cargar_vacio(user, hoy):
            return WidgetData(count=0, items=[], mensaje_vacio="No hay bajas por resolver")

        def cargar_lleno(user, hoy):
            items = [Item(f"Item {i}", "meta", "/x") for i in range(7)]
            return WidgetData(
                count=7,
                items=items,
                cta_url="/cta",
                cta_label="Resolver",
                ver_todos_url="/todos",
                mensaje_vacio="No hay",
            )

        registrar(
            Widget("test.vacio", "Cola vacía", "ventas", "ventas.panel", 2, "bi-x", cargar_vacio)
        )
        registrar(
            Widget("test.lleno", "Cola llena", "ventas", "ventas.panel", 1, "bi-x", cargar_lleno)
        )
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        self.assertContains(response, "Todo al día")
        self.assertContains(response, "No hay bajas por resolver")
        self.assertContains(response, "Item 0")
        self.assertContains(response, "Item 4")
        self.assertNotContains(response, "Item 6")
        self.assertContains(response, "Ver todos (7)")
        self.assertContains(response, "Resolver")

    def test_widget_que_lanza_no_rompe_la_pagina(self):
        def explota(user, hoy):
            raise RuntimeError("boom")

        registrar(Widget("test.boom", "Roto", "ventas", "ventas.panel", 1, "bi-x", explota))
        with patch("api.inicio.servir.logger.exception") as log:
            response = self.http.get(reverse("inicio") + "?ctx=ventas")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pudimos cargar esto")
        log.assert_called()

    def test_orden_pendientes_primero(self):
        def vacio(user, hoy):
            return WidgetData(count=0, items=[], mensaje_vacio="vacío")

        def uno(user, hoy):
            return WidgetData(count=1, items=[Item("A", "", "/")], cta_label="Ir", cta_url="/")

        def tres(user, hoy):
            return WidgetData(count=3, items=[Item("B", "", "/")], cta_label="Ir", cta_url="/")

        registrar(Widget("test.v", "Vacío Z", "ventas", "ventas.panel", 0, "bi-x", vacio))
        registrar(Widget("test.1", "Uno", "ventas", "ventas.panel", 2, "bi-x", uno))
        registrar(Widget("test.3", "Tres", "ventas", "ventas.panel", 2, "bi-x", tres))
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        html = response.content.decode()
        self.assertLess(html.index("Tres"), html.index("Uno"))
        self.assertLess(html.index("Uno"), html.index("Vacío Z"))


class InicioContextosTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.factory = RequestFactory()

    def _request(self, user, path="/inicio/", session=None):
        request = self.factory.get(path)
        request.user = user
        request.session = session if session is not None else {}
        return request

    def test_contextos_disponibles_matriz(self):
        admin = crear_admin()
        superu = User.objects.create_superuser("root", "root@example.com", "secret123")
        vend = crear_vendedor()
        curso = Curso.objects.create(nombre="Álgebra")
        doc = crear_docente(cursos=[curso])
        both = crear_vendedor(username="both.v")
        crear_docente(user=both, cursos=[curso])
        admin_doc = crear_admin("admin.doc")
        crear_docente(user=admin_doc, cursos=[curso], username="admin.doc")
        alum = crear_alumno()
        nadie = User.objects.create_user("nadie", "nadie@example.com", "secret123")

        self.assertEqual(
            [c["clave"] for c in contextos_disponibles(admin)],
            ["escolar", "ventas", "direccion"],
        )
        self.assertEqual(
            [c["clave"] for c in contextos_disponibles(superu)],
            ["escolar", "ventas", "direccion"],
        )
        self.assertEqual([c["clave"] for c in contextos_disponibles(vend)], ["ventas"])
        self.assertEqual([c["clave"] for c in contextos_disponibles(doc)], ["docente"])
        self.assertEqual([c["clave"] for c in contextos_disponibles(both)], ["ventas", "docente"])
        self.assertEqual(
            [c["clave"] for c in contextos_disponibles(admin_doc)],
            ["escolar", "ventas", "docente", "direccion"],
        )
        self.assertEqual(contextos_disponibles(alum), [])
        self.assertEqual(contextos_disponibles(nadie), [])

    def test_admin_abre_escolar_por_defecto(self):
        admin = crear_admin()
        http = Client()
        http.force_login(admin)
        response = http.get(reverse("inicio"))
        self.assertContains(response, "home-tabs")
        self.assertContains(response, "data-home-tabs")
        self.assertContains(response, "Control escolar")
        self.assertContains(response, "Ventas")
        self.assertContains(response, "Dirección")
        self.assertContains(response, 'href="?ctx=escolar"')
        self.assertContains(response, "nav-link active")
        self.assertEqual(http.session.get("inicio_ctx"), "escolar")

    def test_superusuario_abre_direccion(self):
        superu = User.objects.create_superuser("root2", "root2@example.com", "secret123")
        http = Client()
        http.force_login(superu)
        response = http.get(reverse("inicio"))
        self.assertContains(response, "Hoy · Dirección")
        self.assertEqual(http.session.get("inicio_ctx"), "direccion")

    def test_vendedor_docente_abre_ventas(self):
        curso = Curso.objects.create(nombre="Física")
        user = crear_vendedor(username="vd")
        crear_docente(user=user, cursos=[curso], username="vd")
        http = Client()
        http.force_login(user)
        response = http.get(reverse("inicio"))
        self.assertContains(response, "Ventas")
        self.assertContains(response, "Docencia")
        self.assertEqual(http.session.get("inicio_ctx"), "ventas")

    def test_un_solo_contexto_sin_selector(self):
        vend = crear_vendedor(username="solo.v")
        http = Client()
        http.force_login(vend)
        response = http.get(reverse("inicio"))
        self.assertNotContains(response, "home-tabs")
        self.assertEqual(response.status_code, 200)

    def test_ctx_persiste_en_sesion(self):
        curso = Curso.objects.create(nombre="Química")
        user = crear_vendedor(username="sess.v")
        crear_docente(user=user, cursos=[curso], username="sess.v")
        http = Client()
        http.force_login(user)
        http.get(reverse("inicio") + "?ctx=docente")
        self.assertEqual(http.session.get("inicio_ctx"), "docente")
        otra = http.get(reverse("inicio"))
        self.assertEqual(http.session.get("inicio_ctx"), "docente")
        self.assertContains(otra, "Hoy · Docencia")

    def test_ctx_invalido_se_ignora(self):
        vend = crear_vendedor(username="noesc")
        http = Client()
        http.force_login(vend)
        response = http.get(reverse("inicio") + "?ctx=escolar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(http.session.get("inicio_ctx"), "ventas")
        self.assertNotContains(response, "Bajas por resolver")

    def test_sidebar_filtra_por_contexto(self):
        curso = Curso.objects.create(nombre="Biología")
        user = crear_vendedor(username="side.v")
        crear_docente(user=user, cursos=[curso], username="side.v")
        http = Client()
        http.force_login(user)
        docente = http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(docente, "Por calificar")
        self.assertContains(docente, "Aula")
        self.assertNotContains(docente, "Nueva venta")
        ventas = http.get(reverse("inicio") + "?ctx=ventas")
        self.assertContains(ventas, "Nueva venta")
        self.assertContains(ventas, "Registrar pago")
        self.assertNotContains(ventas, "Por calificar")

    def test_contexto_activo_request_factory(self):
        vend = crear_vendedor(username="rf.v")
        request = self._request(vend, "/inicio/?ctx=ventas")
        self.assertEqual(contexto_activo(request), "ventas")
        request2 = self._request(vend, "/inicio/?ctx=nope", session={"inicio_ctx": "ventas"})
        self.assertEqual(contexto_activo(request2), "ventas")


class InicioAterrizajeTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()

    def test_alumno_redirect_campus(self):
        alum = crear_alumno()
        http = Client()
        http.force_login(alum)
        response = http.get(reverse("inicio"))
        self.assertRedirects(response, reverse("campus_inicio"), fetch_redirect_response=False)

    def test_destino_post_login(self):
        alum = crear_alumno(username="alum.login")
        vend = crear_vendedor(username="vend.login")
        doc = crear_docente(username="doc.login", cursos=[Curso.objects.create(nombre="C")])
        admin = crear_admin("admin.login")
        self.assertEqual(destino_post_login(alum), "campus_inicio")
        self.assertEqual(destino_post_login(vend), "inicio")
        self.assertEqual(destino_post_login(doc), "inicio")
        self.assertEqual(destino_post_login(admin), "inicio")

    def test_staff_alumno_ve_mi_campus(self):
        curso = Curso.objects.create(nombre="Campus")
        user = crear_docente(cursos=[curso], username="staff.alum")
        crear_alumno(user=user, username="staff.alum")
        http = Client()
        http.force_login(user)
        response = http.get(reverse("inicio"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mi campus")
        self.assertContains(response, "Ir a mi campus")

    def test_sin_grupos_estado_vacio(self):
        user = User.objects.create_user("hueco", "hueco@example.com", "secret123")
        http = Client()
        http.force_login(user)
        response = http.get(reverse("inicio"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no tiene un módulo asignado")
        self.assertNotContains(response, "Pagos por confirmar")

    def test_sin_tabla_en_inicio(self):
        admin = crear_admin("admin.tabla")
        http = Client()
        http.force_login(admin)
        for ctx in ("escolar", "ventas", "direccion"):
            response = http.get(reverse("inicio") + f"?ctx={ctx}")
            self.assertNotContains(response, "<table")
            self.assertContains(response, "home-tabs")


def _archivo():
    return SimpleUploadedFile("doc.pdf", b"%PDF-1.4 test", content_type="application/pdf")


def _alumno(n, user=None):
    if user is None:
        user = User.objects.create_user(f"al{n}", f"al{n}@ex.com", "secret123")
    return Alumno.objects.create(
        user_id=user.pk,
        nombre=f"Alu{n}",
        apellido="Test",
        email=f"al{n}@ex.com",
        curp=f"{n:018d}"[:18],
        fecha_nacimiento=date(2000, 1, 1),
        estado="activo",
    )


class InicioEscolarTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.admin = crear_admin("esc.admin")
        self.http = Client()
        self.http.force_login(self.admin)
        self.hoy = timezone.localdate()
        self.curso = Curso.objects.create(nombre="Historia")
        self.periodo = Periodo.objects.create(
            nombre="2026-A",
            fecha_inicio=self.hoy - timedelta(days=30),
            fecha_fin=self.hoy + timedelta(days=30),
        )
        self.alumnos = [_alumno(i) for i in range(4)]
        self.inscripciones = [
            Inscripcion.objects.create(alumno=al, curso=self.curso, periodo=self.periodo)
            for al in self.alumnos
        ]

    def _inicio(self):
        return self.http.get(reverse("inicio") + "?ctx=escolar")

    def test_bajas_fifo_y_cta(self):
        from sii.models import SolicitudBaja

        ahora = timezone.now()
        for i, ins in enumerate(self.inscripciones[:3]):
            sol = SolicitudBaja.objects.create(
                inscripcion=ins,
                alumno=ins.alumno,
                motivo=f"Motivo largo {i} " * 5,
                creada_por_id=self.alumnos[i].user_id,
                estado="enviada",
            )
            SolicitudBaja.objects.filter(pk=sol.pk).update(creada_en=ahora - timedelta(days=4 - i))
        SolicitudBaja.objects.create(
            inscripcion=self.inscripciones[3],
            alumno=self.alumnos[3],
            motivo="ya",
            creada_por_id=self.alumnos[3].user_id,
            estado="aprobada",
        )
        response = self._inicio()
        self.assertContains(response, "Bajas por resolver")
        self.assertContains(response, "hace 4 días")
        html = response.content.decode()
        self.assertLess(html.index(str(self.alumnos[0])), html.index(str(self.alumnos[2])))
        self.assertContains(response, "estado=enviada")
        self.assertContains(response, "Resolver")
        bajas_html = html.split("Inscripciones nuevas")[0]
        self.assertNotIn(str(self.alumnos[3]), bajas_html)

    def test_expediente_badge_peligro(self):
        from sii.models import DocumentoExpediente

        doc = DocumentoExpediente.objects.create(
            alumno=self.alumnos[0],
            tipo="identificacion",
            archivo=_archivo(),
            estado="en_revision",
            subido_por_id=self.alumnos[0].user_id,
        )
        DocumentoExpediente.objects.filter(pk=doc.pk).update(subido_en=timezone.now() - timedelta(days=8))
        response = self._inicio()
        self.assertContains(response, "text-bg-danger")
        self.assertContains(response, "Identificación oficial")

    def test_ticket_sin_respuesta_primero(self):
        from campus.models import TicketAyuda, TicketRespuesta

        t1 = TicketAyuda.objects.create(
            alumno=self.alumnos[0], categoria="academico", asunto="Con respuesta", descripcion="x", estado="en_atencion"
        )
        TicketRespuesta.objects.create(ticket=t1, autor_id=self.admin.pk, es_staff=True, cuerpo="ok")
        TicketAyuda.objects.create(
            alumno=self.alumnos[1], categoria="tecnico", asunto="Sin staff", descripcion="y", estado="abierto"
        )
        response = self._inicio()
        html = response.content.decode()
        self.assertLess(html.index("Sin respuesta"), html.index("Con respuesta"))
        self.assertContains(response, "Sin respuesta")

    def test_mensajes_no_leidos(self):
        from campus.models import Hilo, HiloParticipante, MensajeCampus
        from campus.services.mensajes import marcar_hilo_leido

        hilo = Hilo.objects.create(asunto="Ayuda kardex", para_control=True, creado_por_id=self.alumnos[0].user_id)
        HiloParticipante.objects.create(hilo=hilo, user_id=self.alumnos[0].user_id)
        MensajeCampus.objects.create(hilo=hilo, autor_id=self.alumnos[0].user_id, cuerpo="hola")
        response = self._inicio()
        self.assertContains(response, "Ayuda kardex")
        marcar_hilo_leido(self.admin, hilo)
        otra = self._inicio()
        self.assertNotContains(otra, "Ayuda kardex")

    def test_aceptacion_fuera_de_ventana_no_aparece(self):
        response = self._inicio()
        self.assertNotContains(response, "Aceptación de materias")

    def test_aceptacion_conteo(self):
        from sii.models import AceptacionCarga

        self.periodo.ventana_aceptacion_inicio = self.hoy
        self.periodo.ventana_aceptacion_fin = self.hoy
        self.periodo.save()
        extras = [_alumno(20 + i) for i in range(6)]
        extra_ins = [
            Inscripcion.objects.create(alumno=al, curso=self.curso, periodo=self.periodo) for al in extras
        ]
        # 4 originales + 6 extras = 10 activas. 6 aceptadas, 1 cambio → 3 faltan + 1 cambio
        todas = self.inscripciones + extra_ins
        for ins in todas[:6]:
            AceptacionCarga.objects.create(inscripcion=ins, estado="aceptada")
        AceptacionCarga.objects.create(inscripcion=todas[6], estado="cambio")
        response = self._inicio()
        self.assertContains(response, "3 faltan por confirmar")
        self.assertContains(response, "1 pidió cambio")

    def test_acta_borrador(self):
        from sii.models import ActaFinal

        periodo = Periodo.objects.create(
            nombre="pasado",
            fecha_inicio=self.hoy - timedelta(days=60),
            fecha_fin=self.hoy - timedelta(days=1),
            cerrado=False,
        )
        ActaFinal.objects.create(curso=self.curso, periodo=periodo, estado="borrador")
        response = self._inicio()
        self.assertContains(response, "Actas por publicar")
        self.assertContains(response, "Historia")

    def test_todo_al_dia(self):
        Inscripcion.objects.all().delete()
        response = self._inicio()
        self.assertContains(response, "Todo al día en Control escolar")
        self.assertContains(response, reverse("sii_alumnos"))
        self.assertContains(response, reverse("sii_inscripciones"))
        self.assertContains(response, reverse("sii_periodos"))

    def test_vendedor_no_ve_escolar(self):
        vend = crear_vendedor(username="esc.vend")
        http = Client()
        http.force_login(vend)
        response = http.get(reverse("inicio") + "?ctx=escolar")
        self.assertNotContains(response, "Bajas por resolver")
        self.assertEqual(http.session.get("inicio_ctx"), "ventas")


class InicioVentasTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        from ventas.models import Cliente, Producto, Venta, VentaDetalle, Pago, EdicionCurso, SolicitudOferta

        crear_grupos()
        self.vend = crear_vendedor(username="v90")
        self.vendedor = Vendedor.objects.get(user_id=self.vend.pk)
        self.http = Client()
        self.http.force_login(self.vend)
        self.cliente = Cliente.objects.create(
            nombre="Ana", apellidos="Lopez", direccion="Calle 1", email="ana.v90@ex.com"
        )
        self.producto = Producto.objects.create(producto="Inglés", precio_unitario=Decimal("1000"), activo=True)
        self.hoy = timezone.localdate()
        self.Venta = Venta
        self.VentaDetalle = VentaDetalle
        self.Pago = Pago
        self.EdicionCurso = EdicionCurso
        self.SolicitudOferta = SolicitudOferta

    def _venta(self, estado_pago="pendiente", estado="confirmada", fecha=None, vendedor=None, monto=None, descuento=None):
        venta = self.Venta.objects.create(
            id_cliente=self.cliente,
            fecha=fecha or self.hoy,
            estado_pago=estado_pago,
            estado=estado,
            id_vendedor=vendedor,
        )
        self.VentaDetalle.objects.create(
            id_venta=venta,
            id_producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal(str(monto or 1000)),
            descuento=Decimal(str(descuento)) if descuento is not None else None,
        )
        return venta

    def test_pagos_por_confirmar(self):
        vieja = self._venta()
        self.Venta.objects.filter(pk=vieja.pk).update(registrado_en=timezone.now() - timedelta(days=2))
        self._venta()
        parcial = self._venta(estado_pago="parcial", monto=1000)
        self.Pago.objects.create(id_venta=parcial, monto=Decimal("400"), estado="aplicado")
        self._venta(estado="cancelada", estado_pago="pendiente")
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        self.assertContains(response, "Pagos por confirmar")
        self.assertContains(response, "$600")
        self.assertContains(response, "Parcial")
        self.assertContains(response, vieja.folio)
        self.assertNotContains(response, "<table")
        html = response.content.decode()
        self.assertEqual(html.count("V-"), html.count("V-") )  # smoke
        self.assertContains(response, "Registrar pago")
        pagos_html = response.content.decode().split("Folios recientes")[0]
        for venta in self.Venta.objects.filter(estado="cancelada"):
            self.assertNotIn(venta.folio, pagos_html)

    def test_solicitudes_fifo(self):
        alum1 = _alumno(30)
        alum2 = _alumno(31)
        ed = self.EdicionCurso.objects.create(
            id_curso=self.producto,
            codigo_edicion="ING-01",
            fecha_inicio=self.hoy + timedelta(days=5),
            fecha_fin=self.hoy + timedelta(days=90),
            cupo_maximo=20,
            cupo_ocupado=2,
            estado="programada",
            activo=True,
        )
        s1 = self.SolicitudOferta.objects.create(alumno=alum1, edicion=ed, estado="enviada")
        s2 = self.SolicitudOferta.objects.create(alumno=alum2, edicion=ed, estado="enviada")
        self.SolicitudOferta.objects.filter(pk=s1.pk).update(creada_en=timezone.now() - timedelta(days=3))
        self.SolicitudOferta.objects.filter(pk=s2.pk).update(creada_en=timezone.now() - timedelta(days=1))
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        html = response.content.decode()
        self.assertLess(html.index(str(alum1)), html.index(str(alum2)))
        self.assertContains(response, "ING-01")
        self.assertContains(response, "Atender")
        self.assertContains(response, "estado=enviada")

    def test_ediciones_cupo(self):
        self.EdicionCurso.objects.create(
            id_curso=self.producto,
            codigo_edicion="LOW-01",
            fecha_inicio=self.hoy + timedelta(days=5),
            fecha_fin=self.hoy + timedelta(days=40),
            cupo_maximo=20,
            cupo_ocupado=2,
            estado="programada",
            activo=True,
        )
        self.EdicionCurso.objects.create(
            id_curso=self.producto,
            codigo_edicion="FULL-01",
            fecha_inicio=self.hoy + timedelta(days=3),
            fecha_fin=self.hoy + timedelta(days=40),
            cupo_maximo=10,
            cupo_ocupado=10,
            estado="programada",
            activo=True,
        )
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        self.assertContains(response, "2/20")
        self.assertContains(response, "cupo bajo")
        self.assertContains(response, "llena")

    def test_mis_ventas_solo_ficha(self):
        self._venta(estado="confirmada", vendedor=self.vendedor, monto=1500)
        self._venta(estado="confirmada", vendedor=self.vendedor, monto=2000)
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        self.assertContains(response, "Mis ventas de hoy")
        self.assertContains(response, "2 ventas · $3,500")
        admin = crear_admin("v90.admin")
        http = Client()
        http.force_login(admin)
        otra = http.get(reverse("inicio") + "?ctx=ventas")
        self.assertNotContains(otra, "Mis ventas de hoy")

    def test_todo_al_dia_pagos_solicitudes(self):
        response = self.http.get(reverse("inicio") + "?ctx=ventas")
        self.assertContains(response, "No hay pagos por confirmar")
        self.assertContains(response, "No hay solicitudes pendientes")


class InicioDocenteTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        from datetime import time

        from aula.models import Actividad, CalificacionActividad
        from ventas.models import EdicionCurso, Producto

        crear_grupos()
        self.hoy = timezone.localdate()
        self.curso = Curso.objects.create(nombre="Marketing")
        self.ajeno = Curso.objects.create(nombre="Ajeno")
        self.periodo = Periodo.objects.create(
            nombre="Vigente",
            fecha_inicio=self.hoy - timedelta(days=10),
            fecha_fin=self.hoy + timedelta(days=10),
        )
        self.doc_user = crear_docente(cursos=[self.curso], username="d91")
        self.http = Client()
        self.http.force_login(self.doc_user)
        self.producto = Producto.objects.create(
            producto="Marketing", precio_unitario=Decimal("1500"), id_curso=self.curso
        )
        self.edicion = EdicionCurso.objects.create(
            id_curso=self.producto,
            codigo_edicion="MKT-A",
            fecha_inicio=self.hoy - timedelta(days=5),
            fecha_fin=self.hoy + timedelta(days=40),
            estado="en_curso",
            activo=True,
        )
        from sii.models import HorarioSlot

        HorarioSlot.objects.create(
            curso=self.curso,
            periodo=self.periodo,
            dia=self.hoy.isoweekday(),
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            lugar="Aula 1",
        )
        self.Actividad = Actividad
        self.Calificacion = CalificacionActividad
        self.alumnos = [_alumno(40 + i) for i in range(12)]
        self.inscripciones = [
            Inscripcion.objects.create(
                alumno=al, curso=self.curso, periodo=self.periodo, id_edicion=self.edicion, estado="activo"
            )
            for al in self.alumnos
        ]

    def test_clases_hoy(self):
        response = self.http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(response, "09:00–11:00")
        self.assertContains(response, "Marketing")
        self.assertContains(response, "Aula 1")

    def test_por_calificar_agrupa_y_excluye_ajenos(self):
        act_a = self.Actividad.objects.create(
            curso=self.curso, nombre="A", fecha_limite=self.hoy + timedelta(days=2), estado="activa"
        )
        act_b = self.Actividad.objects.create(
            curso=self.curso, nombre="B", fecha_limite=self.hoy + timedelta(days=2), estado="activa"
        )
        act_x = self.Actividad.objects.create(
            curso=self.ajeno, nombre="X", fecha_limite=self.hoy + timedelta(days=2), estado="activa"
        )
        for ins in self.inscripciones[:4]:
            self.Calificacion.objects.create(
                actividad=act_a, inscripcion=ins, entregado=True, fecha_entrega=self.hoy - timedelta(days=3)
            )
        self.Calificacion.objects.create(
            actividad=act_b,
            inscripcion=self.inscripciones[4],
            entregado=True,
            fecha_entrega=self.hoy - timedelta(days=1),
        )
        ins_x = Inscripcion.objects.create(alumno=_alumno(99), curso=self.ajeno, periodo=self.periodo)
        self.Calificacion.objects.create(actividad=act_x, inscripcion=ins_x, entregado=True, fecha_entrega=self.hoy)
        response = self.http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(response, "A · 4 entregas")
        self.assertContains(response, "B · 1")
        self.assertNotContains(response, "X ·")
        self.assertContains(response, reverse("aula_calificar", args=[act_a.pk]).rsplit("/", 2)[0])

    def test_grupos_activos_y_sin_aviso(self):
        response = self.http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(response, "MKT-A")
        self.assertContains(response, "12 alumnos")
        self.assertContains(response, "Grupos sin aviso")
        self.assertContains(response, "Publicar aviso")

    def test_cierran_pronto(self):
        act = self.Actividad.objects.create(
            curso=self.curso, nombre="Ensayo", fecha_limite=self.hoy + timedelta(days=2), estado="activa"
        )
        for ins in self.inscripciones[:3]:
            self.Calificacion.objects.create(actividad=act, inscripcion=ins, entregado=True, fecha_entrega=self.hoy)
        response = self.http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(response, "Cierra en 2 días")
        self.assertContains(response, "3/12 entregas")

    def test_docente_sin_asignaciones(self):
        user = crear_docente(cursos=[], username="d91.solo")
        http = Client()
        http.force_login(user)
        response = http.get(reverse("inicio"))
        self.assertContains(response, "Aún no tienes grupos asignados")

    def test_sin_ficha_no_hay_contexto_docente(self):
        vend = crear_vendedor(username="d91.vend")
        http = Client()
        http.force_login(vend)
        response = http.get(reverse("inicio") + "?ctx=docente")
        self.assertEqual(http.session.get("inicio_ctx"), "ventas")
        self.assertNotContains(response, "Mis clases de hoy")

    def test_admin_con_ficha_solo_sus_cursos(self):
        admin = crear_admin("d91.admin")
        crear_docente(user=admin, cursos=[self.curso], username="d91.admin")
        http = Client()
        http.force_login(admin)
        response = http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(response, "Marketing")
        self.assertNotContains(response, "Ajeno")

    def test_admin_con_ficha_grupos_y_sin_aviso_solo_docente_curso(self):
        from ventas.models import EdicionCurso, Producto

        producto_ajeno = Producto.objects.create(
            producto="Ajeno", precio_unitario=Decimal("900"), id_curso=self.ajeno
        )
        EdicionCurso.objects.create(
            id_curso=producto_ajeno,
            codigo_edicion="AJENO-1",
            fecha_inicio=self.hoy - timedelta(days=5),
            fecha_fin=self.hoy + timedelta(days=40),
            estado="en_curso",
            activo=True,
        )
        admin = crear_admin("d91.admin.g")
        crear_docente(user=admin, cursos=[self.curso], username="d91.admin.g")
        http = Client()
        http.force_login(admin)
        response = http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(response, "MKT-A")
        self.assertNotContains(response, "AJENO-1")
        self.assertContains(response, "Grupos sin aviso")


class InicioDireccionTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.admin = crear_admin("dir.admin")
        self.http = Client()
        self.http.force_login(self.admin)
        self.hoy = timezone.localdate()

    def test_cuatro_tarjetas_y_kpi_mes(self):
        from ventas.models import Cliente, Producto, Venta, VentaDetalle, Pago

        cliente = Cliente.objects.create(nombre="Dir", apellidos="Kpi", direccion="x", email="dir.kpi@ex.com")
        producto = Producto.objects.create(producto="X", precio_unitario=Decimal("1000"))
        venta = Venta.objects.create(id_cliente=cliente, fecha=self.hoy, estado="confirmada", estado_pago="pagado")
        VentaDetalle.objects.create(id_venta=venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("12000"))
        pago = Pago.objects.create(id_venta=venta, monto=Decimal("12000"), estado="aplicado")
        Pago.objects.filter(pk=pago.pk).update(fecha_pago=timezone.now())
        venta_old = Venta.objects.create(
            id_cliente=cliente, fecha=self.hoy.replace(day=1) - timedelta(days=2), estado="confirmada", estado_pago="pagado"
        )
        VentaDetalle.objects.create(
            id_venta=venta_old, id_producto=producto, cantidad=1, precio_unitario=Decimal("5000")
        )
        pago_old = Pago.objects.create(id_venta=venta_old, monto=Decimal("5000"), estado="aplicado")
        Pago.objects.filter(pk=pago_old.pk).update(fecha_pago=timezone.now() - timedelta(days=40))
        response = self.http.get(reverse("inicio") + "?ctx=direccion")
        self.assertContains(response, "$12,000 cobrados")
        self.assertNotContains(response, "$5,000 cobrados")
        self.assertContains(response, "Ir a Ventas")
        self.assertContains(response, "Ir a Control escolar")
        self.assertContains(response, "Ir a Aula")
        self.assertContains(response, "home-kpi")
        html = response.content.decode()
        self.assertLess(html.index(">Ventas<"), html.index("Control escolar"))
        self.assertNotContains(response, "<table")

    def test_tramites_y_alerta_cero(self):
        from campus.models import TicketAyuda
        from sii.models import DocumentoExpediente, SolicitudBaja

        curso = Curso.objects.create(nombre="T")
        periodo = Periodo.objects.create(nombre="P", fecha_inicio=self.hoy, fecha_fin=self.hoy + timedelta(days=1))
        alumnos = [_alumno(50 + i) for i in range(3)]
        ins = [
            Inscripcion.objects.create(alumno=al, curso=curso, periodo=periodo) for al in alumnos
        ]
        for inscripcion in ins[:2]:
            SolicitudBaja.objects.create(
                inscripcion=inscripcion,
                alumno=inscripcion.alumno,
                motivo="x",
                creada_por_id=inscripcion.alumno.user_id,
                estado="enviada",
            )
        DocumentoExpediente.objects.create(
            alumno=alumnos[0],
            tipo="otro",
            archivo=_archivo(),
            estado="en_revision",
            subido_por_id=alumnos[0].user_id,
        )
        for i in range(3):
            TicketAyuda.objects.create(
                alumno=alumnos[0], categoria="otro", asunto=f"t{i}", descripcion="d", estado="abierto"
            )
        response = self.http.get(reverse("inicio") + "?ctx=direccion")
        self.assertContains(response, "6 trámites abiertos")
        self.assertContains(response, "?ctx=escolar")
        self.assertNotContains(response, "0 actas atrasadas")

    def test_kpis_booleanos_con_orm(self):
        import inspect

        from api.inicio import widgets_direccion
        from campus.models import AvisoInstitucional
        from sii.models import ActaFinal

        fuente = inspect.getsource(widgets_direccion)
        self.assertNotIn("cursor.execute", fuente)
        self.assertNotIn("cerrado = 0", fuente)
        self.assertNotIn("publicado = 1", fuente)
        self.assertIn("cerrado=False", fuente)
        self.assertIn("publicado=True", fuente)

        curso = Curso.objects.create(nombre="ActaDir")
        abierto = Periodo.objects.create(
            nombre="Abierto",
            fecha_inicio=self.hoy - timedelta(days=60),
            fecha_fin=self.hoy - timedelta(days=1),
            cerrado=False,
        )
        cerrado = Periodo.objects.create(
            nombre="Cerrado",
            fecha_inicio=self.hoy - timedelta(days=120),
            fecha_fin=self.hoy - timedelta(days=30),
            cerrado=True,
        )
        ActaFinal.objects.create(curso=curso, periodo=abierto, estado="borrador")
        ActaFinal.objects.create(
            curso=Curso.objects.create(nombre="ActaCerrada"),
            periodo=cerrado,
            estado="borrador",
        )
        AvisoInstitucional.objects.create(
            titulo="Urgente",
            cuerpo="x",
            tipo=AvisoInstitucional.TIPO_IMPORTANTE,
            publicado=True,
            vigencia_inicio=self.hoy - timedelta(days=1),
            vigencia_fin=self.hoy + timedelta(days=1),
        )
        AvisoInstitucional.objects.create(
            titulo="Borrador",
            cuerpo="x",
            tipo=AvisoInstitucional.TIPO_IMPORTANTE,
            publicado=False,
        )
        kpis = widgets_direccion._kpis(self.admin, self.hoy)
        self.assertEqual(kpis["actas"], 1)
        self.assertEqual(kpis["avisos"], 1)
        response = self.http.get(reverse("inicio") + "?ctx=direccion")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 actas atrasadas")
        self.assertContains(response, "1 avisos importantes vigentes")
        self.assertNotContains(response, "No pudimos cargar esto")

    def test_vendedor_sin_direccion(self):
        vend = crear_vendedor(username="dir.vend")
        http = Client()
        http.force_login(vend)
        response = http.get(reverse("inicio") + "?ctx=direccion")
        self.assertNotContains(response, "trámites abiertos")
        self.assertEqual(http.session.get("inicio_ctx"), "ventas")


class InicioFranjaTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()

    def test_franja_por_contexto(self):
        import inspect

        from api.inicio import conteos

        fuente = inspect.getsource(conteos)
        self.assertNotIn("cursor.execute", fuente)
        self.assertNotIn("activo = 1", fuente)
        self.assertNotIn("activo = 0", fuente)
        self.assertIn("activo=True", fuente)

        admin = crear_admin("franja.admin")
        http = Client()
        http.force_login(admin)
        ventas = http.get(reverse("inicio") + "?ctx=ventas")
        self.assertEqual(ventas.status_code, 200)
        self.assertContains(ventas, "Clientes activos")
        self.assertContains(ventas, "Cursos en venta")
        self.assertContains(ventas, "Ediciones abiertas")
        escolar = http.get(reverse("inicio") + "?ctx=escolar")
        self.assertContains(escolar, "Alumnos activos")
        self.assertContains(escolar, "Inscripciones")
        self.assertContains(escolar, "Docentes")
        direccion = http.get(reverse("inicio") + "?ctx=direccion")
        self.assertNotContains(direccion, "Clientes activos")
        self.assertNotContains(direccion, "Alumnos activos")

    def test_docente_cuenta_sus_alumnos(self):
        curso = Curso.objects.create(nombre="F")
        user = crear_docente(cursos=[curso], username="franja.doc")
        propio = _alumno(70)
        Periodo.objects.create(nombre="p", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 6, 1))
        periodo = Periodo.objects.first()
        Inscripcion.objects.create(alumno=propio, curso=curso, periodo=periodo)
        _alumno(71)
        http = Client()
        http.force_login(user)
        response = http.get(reverse("inicio") + "?ctx=docente")
        self.assertContains(response, "Mis grupos")
        self.assertContains(response, "Mis alumnos")
        self.assertContains(response, ">1</strong>")

    def test_mi_campus_solo_staff_alumno(self):
        vend = crear_vendedor(username="franja.vend")
        http = Client()
        http.force_login(vend)
        self.assertNotContains(http.get(reverse("inicio")), "Mi campus")


class InicioFiltrosTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.admin = crear_admin("fil.admin")
        self.http = Client()
        self.http.force_login(self.admin)
        self.hoy = timezone.localdate()
        self.curso = Curso.objects.create(nombre="Filtro")
        self.periodo = Periodo.objects.create(
            nombre="F", fecha_inicio=self.hoy - timedelta(days=1), fecha_fin=self.hoy + timedelta(days=10)
        )

    def test_bajas_filtro(self):
        from sii.models import SolicitudBaja

        al = _alumno(80)
        ins = Inscripcion.objects.create(alumno=al, curso=self.curso, periodo=self.periodo)
        enviada = SolicitudBaja.objects.create(
            inscripcion=ins, alumno=al, motivo="e", creada_por_id=al.user_id, estado="enviada"
        )
        al2 = _alumno(81)
        ins2 = Inscripcion.objects.create(alumno=al2, curso=self.curso, periodo=self.periodo)
        aprobada = SolicitudBaja.objects.create(
            inscripcion=ins2, alumno=al2, motivo="a", creada_por_id=al2.user_id, estado="aprobada"
        )
        filtrada = self.http.get(reverse("sii_solicitudes_baja") + "?estado=enviada")
        self.assertContains(filtrada, enviada.alumno.nombre)
        self.assertNotContains(filtrada, aprobada.alumno.nombre)
        self.assertContains(filtrada, "Filtrado: enviada")
        invalida = self.http.get(reverse("sii_solicitudes_baja") + "?estado=xyz")
        self.assertEqual(invalida.status_code, 200)
        self.assertContains(invalida, aprobada.alumno.nombre)
        todas = self.http.get(reverse("sii_solicitudes_baja"))
        self.assertContains(todas, enviada.alumno.nombre)
        self.assertContains(todas, aprobada.alumno.nombre)

    def test_expediente_ayuda_oferta_pagos(self):
        from campus.models import TicketAyuda
        from sii.models import DocumentoExpediente
        from ventas.models import Cliente, Producto, SolicitudOferta, EdicionCurso, Venta, VentaDetalle

        al = _alumno(82)
        DocumentoExpediente.objects.create(
            alumno=al, tipo="otro", archivo=_archivo(), estado="en_revision", subido_por_id=al.user_id
        )
        DocumentoExpediente.objects.create(
            alumno=_alumno(83), tipo="otro", archivo=_archivo(), estado="aceptado", subido_por_id=al.user_id
        )
        rev = self.http.get(reverse("sii_expediente") + "?estado=en_revision")
        self.assertContains(rev, "Alu82")
        self.assertNotContains(rev, "Alu83")
        TicketAyuda.objects.create(alumno=al, categoria="otro", asunto="abierto", descripcion="d", estado="abierto")
        TicketAyuda.objects.create(
            alumno=al, categoria="otro", asunto="cerrado", descripcion="d", estado="cerrado"
        )
        ayuda = self.http.get(reverse("sii_ayuda") + "?estado=abierto,en_atencion")
        self.assertContains(ayuda, "abierto")
        self.assertNotContains(ayuda, "cerrado")
        producto = Producto.objects.create(producto="P", precio_unitario=Decimal("1"))
        ed = EdicionCurso.objects.create(
            id_curso=producto, codigo_edicion="E1", fecha_inicio=self.hoy, fecha_fin=self.hoy, estado="programada"
        )
        SolicitudOferta.objects.create(alumno=al, edicion=ed, estado="enviada")
        ofertas = self.http.get(reverse("ventas_solicitudes_oferta") + "?estado=enviada")
        self.assertContains(ofertas, str(al))
        cliente = Cliente.objects.create(nombre="C", apellidos="P", direccion="d", email="c.fil@ex.com")
        venta = Venta.objects.create(id_cliente=cliente, fecha=self.hoy, estado="confirmada", estado_pago="pendiente")
        VentaDetalle.objects.create(id_venta=venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("10"))
        pagos = self.http.get(reverse("Pagos") + f"?venta={venta.pk}")
        self.assertContains(pagos, venta.folio or str(venta.pk))
        self.assertContains(pagos, f'value="{venta.pk}"')

    def test_aceptaciones_pendiente(self):
        from sii.models import AceptacionCarga

        al = _alumno(84)
        ins = Inscripcion.objects.create(alumno=al, curso=self.curso, periodo=self.periodo, estado="activo")
        self.periodo.ventana_aceptacion_inicio = self.hoy
        self.periodo.ventana_aceptacion_fin = self.hoy
        self.periodo.save()
        abierta = self.http.get(reverse("sii_aceptaciones") + "?pendiente=1")
        self.assertContains(abierta, al.nombre)
        AceptacionCarga.objects.create(inscripcion=ins, estado="aceptada")
        sin = self.http.get(reverse("sii_aceptaciones") + "?pendiente=1")
        self.assertNotContains(sin, al.nombre)
        self.periodo.ventana_aceptacion_inicio = self.hoy - timedelta(days=10)
        self.periodo.ventana_aceptacion_fin = self.hoy - timedelta(days=9)
        self.periodo.save()
        cerrada = self.http.get(reverse("sii_aceptaciones") + "?pendiente=1")
        self.assertNotContains(cerrada, al.nombre)


class InicioMatrizYQueriesTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()

    def test_matriz_roles(self):
        curso = Curso.objects.create(nombre="Matriz")
        alum = crear_alumno(username="mx.alum")
        vend = crear_vendedor(username="mx.vend")
        doc = crear_docente(cursos=[curso], username="mx.doc")
        admin = crear_admin("mx.admin")
        superu = User.objects.create_superuser("mx.root", "mx.root@ex.com", "secret123")
        both = crear_vendedor(username="mx.both")
        crear_docente(user=both, cursos=[curso], username="mx.both")
        admin_doc = crear_admin("mx.ad")
        crear_docente(user=admin_doc, cursos=[curso], username="mx.ad")
        staff_al = crear_docente(cursos=[curso], username="mx.sa")
        crear_alumno(user=staff_al, username="mx.sa")
        nadie = User.objects.create_user("mx.none", "mx.none@ex.com", "secret123")

        def get(user, path=reverse("inicio")):
            http = Client()
            http.force_login(user)
            return http.get(path)

        self.assertRedirects(get(alum), reverse("campus_inicio"), fetch_redirect_response=False)
        r_vend = get(vend)
        self.assertEqual(r_vend.status_code, 200)
        self.assertNotContains(r_vend, "home-tabs")
        self.assertContains(r_vend, "Mis ventas de hoy")
        r_doc = get(doc)
        self.assertEqual(r_doc.status_code, 200)
        self.assertNotContains(r_doc, "home-tabs")
        self.assertContains(r_doc, "Docencia")
        r_admin = get(admin)
        self.assertContains(r_admin, "home-tabs")
        self.assertContains(r_admin, "Control escolar")
        self.assertEqual(r_admin.wsgi_request.session.get("inicio_ctx"), "escolar")
        r_root = get(superu)
        self.assertContains(r_root, "Hoy · Dirección")
        r_both = get(both)
        self.assertContains(r_both, "Ventas")
        self.assertContains(r_both, "Docencia")
        self.assertEqual(r_both.wsgi_request.session.get("inicio_ctx"), "ventas")
        r_ad = get(admin_doc)
        for label in ("Control escolar", "Ventas", "Docencia", "Dirección"):
            self.assertContains(r_ad, label)
        r_sa = get(staff_al)
        self.assertContains(r_sa, "Mi campus")
        r_none = get(nadie)
        self.assertContains(r_none, "no tiene un módulo asignado")
        for ctx in ("escolar", "ventas", "direccion"):
            self.assertNotContains(get(admin, reverse("inicio") + f"?ctx={ctx}"), "<table")
        self.assertNotContains(get(vend, reverse("inicio") + "?ctx=escolar"), "Bajas por resolver")

    def test_presupuesto_queries(self):
        from django.db import connections
        from django.test.utils import CaptureQueriesContext
        from sii.models import ActaFinal, DocumentoExpediente, SolicitudBaja
        from campus.models import TicketAyuda
        from ventas.models import Cliente, Producto, Venta, VentaDetalle

        admin = crear_admin("q.admin")
        crear_docente(user=admin, cursos=[Curso.objects.create(nombre="Q")], username="q.admin")
        hoy = timezone.localdate()
        curso = Curso.objects.first()
        periodo = Periodo.objects.create(
            nombre="Q", fecha_inicio=hoy - timedelta(days=20), fecha_fin=hoy - timedelta(days=1), cerrado=False
        )
        producto = Producto.objects.create(producto="QP", precio_unitario=Decimal("10"), id_curso=curso)
        cliente = Cliente.objects.create(nombre="Q", apellidos="C", direccion="d", email="q.c@ex.com")
        for i in range(20):
            al = _alumno(200 + i)
            ins = Inscripcion.objects.create(alumno=al, curso=curso, periodo=periodo)
            SolicitudBaja.objects.create(
                inscripcion=ins, alumno=al, motivo="m", creada_por_id=al.user_id, estado="enviada"
            )
            DocumentoExpediente.objects.create(
                alumno=al, tipo="otro", archivo=_archivo(), estado="en_revision", subido_por_id=al.user_id
            )
            TicketAyuda.objects.create(
                alumno=al, categoria="otro", asunto=f"t{i}", descripcion="d", estado="abierto"
            )
            ActaFinal.objects.get_or_create(curso=curso, periodo=periodo, defaults={"estado": "borrador"})
            venta = Venta.objects.create(
                id_cliente=cliente, fecha=hoy, estado="confirmada", estado_pago="pendiente"
            )
            VentaDetalle.objects.create(
                id_venta=venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("10")
            )
        http = Client()
        http.force_login(admin)
        http.get(reverse("inicio") + "?ctx=escolar")

        def contar(ctx):
            with CaptureQueriesContext(connections["default"]) as cap:
                http.get(reverse("inicio") + f"?ctx={ctx}")
            return len(cap)

        n1 = contar("escolar")
        n2 = contar("ventas")
        n3 = contar("docente")
        n4 = contar("direccion")
        self.assertLessEqual(n1, QUERY_BUDGET_INICIO, f"escolar {n1} queries: presupuesto {QUERY_BUDGET_INICIO}")
        self.assertLessEqual(n2, QUERY_BUDGET_INICIO, f"ventas {n2}")
        self.assertLessEqual(n3, QUERY_BUDGET_INICIO, f"docente {n3}")
        self.assertLessEqual(n4, QUERY_BUDGET_INICIO, f"direccion {n4}")
        for i in range(20):
            al = _alumno(300 + i)
            ins = Inscripcion.objects.create(alumno=al, curso=curso, periodo=periodo)
            SolicitudBaja.objects.create(
                inscripcion=ins, alumno=al, motivo="m", creada_por_id=al.user_id, estado="enviada"
            )
        n1b = contar("escolar")
        self.assertEqual(n1, n1b)

    def test_shell_no_repite_pagos(self):
        from django.db import connections
        from django.test.utils import CaptureQueriesContext
        from ventas.models import Cliente, Producto, Venta, VentaDetalle

        vend = crear_vendedor(username="q.vend")
        cliente = Cliente.objects.create(nombre="S", apellidos="H", direccion="d", email="sh@ex.com")
        producto = Producto.objects.create(producto="S", precio_unitario=Decimal("1"))
        venta = Venta.objects.create(id_cliente=cliente, fecha=timezone.localdate(), estado_pago="pendiente")
        VentaDetalle.objects.create(id_venta=venta, id_producto=producto, cantidad=1, precio_unitario=Decimal("1"))
        http = Client()
        http.force_login(vend)
        with CaptureQueriesContext(connections["default"]) as cap:
            http.get(reverse("inicio") + "?ctx=ventas")
        sqls = [q["sql"] for q in cap]
        pagos = [s for s in sqls if "tra_venta" in s.lower() and "estado_pago" in s.lower()]
        self.assertLessEqual(len(pagos), 3)
