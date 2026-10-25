from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from aula.models import Actividad, CalificacionActividad, Recurso, SeccionTema
from aula.services import actualizar_kardex
from aula.storage import LOCAL_BACKEND, S3_BACKEND, backend_archivos
from sii.models import Alumno, Curso, Docente, DocenteCurso, Inscripcion, Periodo
from sii.permissions import GRUPO_ALUMNO, GRUPO_DOCENTE, crear_grupos
from ventas.models import EdicionCurso, Producto


class AulaActividadTests(TestCase):
    databases = {"default", "auth"}

    def setUp(self):
        crear_grupos()
        self.periodo = Periodo.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )
        self.curso = Curso.objects.create(nombre="Marketing", descripcion="Grupo A")
        self.alumno_user = User.objects.create_user("alum", "alum@example.com", "secret123")
        self.docente_user = User.objects.create_user("profe", "profe@example.com", "secret123")
        self.alumno_user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        self.docente_user.groups.add(Group.objects.get(name=GRUPO_DOCENTE))
        self.alumno = Alumno.objects.create(
            user_id=self.alumno_user.pk,
            nombre="Ana",
            apellido="Lopez",
            curp="LOPA000101MDFXXX01",
            email="alum@example.com",
            fecha_nacimiento=date(2000, 1, 1),
        )
        self.docente = Docente.objects.create(
            user_id=self.docente_user.pk,
            nombre="Carlos",
            apellido="Ruiz",
            email="profe@example.com",
        )
        DocenteCurso.objects.create(docente=self.docente, curso=self.curso)
        self.inscripcion = Inscripcion.objects.create(
            alumno=self.alumno,
            curso=self.curso,
            periodo=self.periodo,
        )
        self.producto = Producto.objects.create(
            producto="Marketing",
            precio_unitario=Decimal("1500"),
            id_curso=self.curso,
        )
        self.edicion = EdicionCurso.objects.create(
            id_curso=self.producto,
            codigo_edicion="MKT-A",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.inscripcion.id_edicion = self.edicion
        self.inscripcion.save(update_fields=["id_edicion"])
        self.http_alum = Client()
        self.http_alum.force_login(self.alumno_user)
        self.http_profe = Client()
        self.http_profe.force_login(self.docente_user)

    def test_alumno_no_crea_actividad(self):
        response = self.http_alum.post(
            reverse("aula_actividad_nueva", args=[self.curso.pk]),
            {
                "nombre": "Tarea 1",
                "fecha_limite": (timezone.localdate() + timedelta(days=3)).isoformat(),
                "valor": "100",
                "tipo": "tarea",
                "estado": "activa",
            },
        )
        self.assertEqual(Actividad.objects.count(), 0)
        self.assertEqual(response.status_code, 403)

    def test_docente_crea_alumno_entrega_y_kardex(self):
        response = self.http_profe.post(
            reverse("aula_actividad_nueva", args=[self.curso.pk]),
            {
                "nombre": "Ensayo",
                "descripcion": "Escribe un ensayo",
                "fecha_limite": (timezone.localdate() + timedelta(days=5)).isoformat(),
                "valor": "100",
                "tipo": "tarea",
                "estado": "activa",
            },
        )
        self.assertRedirects(response, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        actividad = Actividad.objects.get()
        self.assertEqual(actividad.edicion_id, self.edicion.pk)
        entregar = self.http_alum.post(
            reverse("aula_entregar", args=[actividad.pk]),
            {"entrega": "Mi ensayo"},
        )
        self.assertRedirects(entregar, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        registro = CalificacionActividad.objects.get(actividad=actividad, inscripcion=self.inscripcion)
        self.assertTrue(registro.entregado)
        prefix = str(self.inscripcion.pk)
        calificar = self.http_profe.post(
            reverse("aula_guardar_calificacion", args=[actividad.pk, self.inscripcion.pk]),
            {f"{prefix}-calificacion": "80", f"{prefix}-comentarios": "Bien"},
        )
        self.assertRedirects(calificar, reverse("aula_calificar", args=[actividad.pk]))
        self.inscripcion.refresh_from_db()
        self.assertEqual(self.inscripcion.calificacion, Decimal("80.00"))
        kardex = self.http_alum.get(reverse("sii_kardex"))
        self.assertContains(kardex, "80")
        redirect = self.http_alum.get(reverse("aula_kardex"))
        self.assertRedirects(redirect, reverse("sii_kardex"))

    def test_sidebar_aula_ya_no_lista_kardex(self):
        response = self.http_alum.get(reverse("aula_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Kardex")

    def test_pendiente_de_pago_bloquea_entrega(self):
        self.inscripcion.puede_cursar = False
        self.inscripcion.save(update_fields=["puede_cursar"])
        actividad = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            nombre="Tarea paga",
            fecha_limite=date.today(),
            valor=Decimal("10"),
        )
        response = self.http_alum.post(
            reverse("aula_entregar", args=[actividad.pk]),
            {"entrega": "No debería entrar"},
        )
        self.assertRedirects(response, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertFalse(CalificacionActividad.objects.filter(actividad=actividad, entregado=True).exists())

    def test_por_calificar_y_guardar_todas(self):
        actividad = Actividad.objects.create(
            curso=self.curso, nombre="Ensayo", fecha_limite=date.today(), valor=Decimal("100")
        )
        CalificacionActividad.objects.create(
            actividad=actividad, inscripcion=self.inscripcion, entregado=True, entrega="Listo"
        )
        pendientes = self.http_profe.get(reverse("aula_por_calificar"))
        self.assertEqual(pendientes.status_code, 200)
        self.assertContains(pendientes, "Ana Lopez")
        prefix = str(self.inscripcion.pk)
        guardar = self.http_profe.post(
            reverse("aula_guardar_calificaciones", args=[actividad.pk]),
            {f"{prefix}-calificacion": "88", f"{prefix}-comentarios": "Ok"},
        )
        self.assertRedirects(guardar, reverse("aula_calificar", args=[actividad.pk]))
        self.inscripcion.refresh_from_db()
        self.assertEqual(self.inscripcion.calificacion, Decimal("88.00"))

    def test_asignar_docente_redirige_a_sii(self):
        response = self.http_profe.get(reverse("aula_asignar_docente", args=[self.curso.pk]))
        self.assertEqual(response.status_code, 403)
        admin = User.objects.create_superuser("admin_aula", "admin.aula@example.com", "secret123")
        http = Client()
        http.force_login(admin)
        redir = http.get(reverse("aula_asignar_docente", args=[self.curso.pk]))
        self.assertRedirects(redir, reverse("sii_docentes"))

    def test_alumno_no_entra_a_calificar(self):
        actividad = Actividad.objects.create(
            curso=self.curso, nombre="Quiz", fecha_limite=date.today(), valor=Decimal("10")
        )
        response = self.http_alum.get(reverse("aula_calificar", args=[actividad.pk]))
        self.assertEqual(response.status_code, 403)

    def test_actualizar_kardex_ponderado(self):
        a1 = Actividad.objects.create(
            curso=self.curso, nombre="A", fecha_limite=date.today(), valor=Decimal("50")
        )
        a2 = Actividad.objects.create(
            curso=self.curso, nombre="B", fecha_limite=date.today(), valor=Decimal("50")
        )
        CalificacionActividad.objects.create(
            actividad=a1, inscripcion=self.inscripcion, calificacion=Decimal("50")
        )
        CalificacionActividad.objects.create(
            actividad=a2, inscripcion=self.inscripcion, calificacion=Decimal("40")
        )
        promedio = actualizar_kardex(self.inscripcion)
        self.assertEqual(promedio, Decimal("90.00"))

    def test_crear_seccion_y_recurso(self):
        crear = self.http_profe.post(
            reverse("aula_seccion_nueva_grupo", args=[self.curso.pk, self.edicion.pk]),
            {"titulo": "Unidad 1", "descripcion": "Introducción", "orden": "1"},
        )
        self.assertRedirects(crear, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        seccion = SeccionTema.objects.get()
        self.assertEqual(seccion.edicion_id, self.edicion.pk)
        recurso = self.http_profe.post(
            reverse("aula_recurso_nuevo", args=[seccion.pk]),
            {
                "titulo": "Guía",
                "tipo": "texto",
                "cuerpo": "<p>Leer el capítulo 1</p>",
                "orden": "1",
                "url": "",
            },
        )
        self.assertRedirects(recurso, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertTrue(Recurso.objects.filter(seccion=seccion, titulo="Guía").exists())
        pagina = self.http_alum.get(reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertContains(pagina, "Unidad 1")
        self.assertContains(pagina, "Guía")
        self.assertNotContains(pagina, "Inscritos del grupo")
        aula_profe = self.http_profe.get(reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertContains(aula_profe, "Inscritos del grupo")
        self.assertContains(aula_profe, "Ana Lopez")

    def test_entrega_bloqueada_por_fecha_y_estado(self):
        vencida = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            nombre="Tarde",
            fecha_limite=timezone.localdate() - timedelta(days=1),
            valor=Decimal("10"),
            estado="activa",
        )
        self.assertFalse(vencida.acepta_entregas())
        r1 = self.http_alum.post(
            reverse("aula_entregar", args=[vencida.pk]),
            {"entrega": "Fuera de tiempo"},
        )
        self.assertRedirects(r1, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertFalse(CalificacionActividad.objects.filter(actividad=vencida, entregado=True).exists())
        cerrada = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            nombre="Cerrada",
            fecha_limite=timezone.localdate() + timedelta(days=5),
            valor=Decimal("10"),
            estado="cerrada",
        )
        r2 = self.http_alum.post(
            reverse("aula_entregar", args=[cerrada.pk]),
            {"entrega": "Tampoco"},
        )
        self.assertRedirects(r2, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertFalse(CalificacionActividad.objects.filter(actividad=cerrada, entregado=True).exists())

    def test_alumno_otro_grupo_no_ve_ni_entrega(self):
        edicion_b = EdicionCurso.objects.create(
            id_curso=self.producto,
            codigo_edicion="MKT-B",
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 12, 15),
        )
        otro_user = User.objects.create_user("otro", "otro@example.com", "secret123")
        otro_user.groups.add(Group.objects.get(name=GRUPO_ALUMNO))
        otro = Alumno.objects.create(
            user_id=otro_user.pk,
            nombre="Beto",
            apellido="Diaz",
            curp="DIBE000101HDFXXX03",
            email="otro@example.com",
            fecha_nacimiento=date(2000, 2, 2),
        )
        periodo_b = Periodo.objects.create(
            nombre="2026-B",
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 12, 31),
        )
        Inscripcion.objects.create(
            alumno=otro,
            curso=self.curso,
            periodo=periodo_b,
            id_edicion=edicion_b,
        )
        seccion = SeccionTema.objects.create(
            curso=self.curso, edicion=self.edicion, titulo="Solo A", orden=1
        )
        actividad = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            seccion=seccion,
            nombre="Tarea A",
            fecha_limite=timezone.localdate() + timedelta(days=3),
            valor=Decimal("20"),
        )
        http_otro = Client()
        http_otro.force_login(otro_user)
        ajeno = http_otro.get(reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertEqual(ajeno.status_code, 404)
        entregar = http_otro.post(
            reverse("aula_entregar", args=[actividad.pk]),
            {"entrega": "No es mi grupo"},
        )
        self.assertEqual(entregar.status_code, 302)
        self.assertFalse(
            CalificacionActividad.objects.filter(actividad=actividad, entregado=True).exists()
        )
        propia = http_otro.get(reverse("aula_grupo", args=[self.curso.pk, edicion_b.pk]))
        self.assertEqual(propia.status_code, 200)
        self.assertNotContains(propia, "Tarea A")
        self.assertNotContains(propia, "Solo A")
        roster_a = self.http_profe.get(reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        self.assertContains(roster_a, "Ana Lopez")
        self.assertNotContains(roster_a, "Beto Diaz")
        roster_b = self.http_profe.get(reverse("aula_grupo", args=[self.curso.pk, edicion_b.pk]))
        self.assertContains(roster_b, "Beto Diaz")
        self.assertNotContains(roster_b, "Ana Lopez")

    def test_alumno_no_crea_seccion(self):
        response = self.http_alum.post(
            reverse("aula_seccion_nueva_grupo", args=[self.curso.pk, self.edicion.pk]),
            {"titulo": "Hack", "orden": "1"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SeccionTema.objects.count(), 0)

    def test_storage_elige_neon_con_keys(self):
        self.assertEqual(
            backend_archivos(
                endpoint="https://br.example.neon.tech",
                access_key="key",
                secret_key="secret",
            ),
            S3_BACKEND,
        )
        self.assertEqual(
            backend_archivos(endpoint="", access_key="", secret_key=""),
            LOCAL_BACKEND,
        )
        self.assertEqual(
            backend_archivos(
                endpoint="https://br.example.neon.tech",
                access_key="key",
                secret_key="secret",
                force_local=True,
            ),
            LOCAL_BACKEND,
        )

    def test_storage_local_sin_credenciales(self):
        self.assertEqual(settings.STORAGES["default"]["BACKEND"], LOCAL_BACKEND)
        archivo = SimpleUploadedFile("nota.txt", b"hola", content_type="text/plain")
        actividad = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            nombre="Con archivo",
            fecha_limite=timezone.localdate() + timedelta(days=2),
            valor=Decimal("10"),
        )
        entrega = self.http_alum.post(
            reverse("aula_entregar", args=[actividad.pk]),
            {"entrega": "Adjunto", "archivo": archivo},
        )
        self.assertRedirects(entrega, reverse("aula_grupo", args=[self.curso.pk, self.edicion.pk]))
        registro = CalificacionActividad.objects.get(actividad=actividad)
        self.assertTrue(registro.archivo)

    def test_hoy_docente_atajo_por_calificar(self):
        actividad = Actividad.objects.create(
            curso=self.curso,
            edicion=self.edicion,
            nombre="Ensayo",
            fecha_limite=date.today(),
            valor=Decimal("100"),
        )
        CalificacionActividad.objects.create(
            actividad=actividad, inscripcion=self.inscripcion, entregado=True, entrega="Listo"
        )
        hoy = self.http_profe.get(reverse("inicio"))
        self.assertContains(hoy, "Por calificar")
        self.assertContains(hoy, "Entregas sin nota")

