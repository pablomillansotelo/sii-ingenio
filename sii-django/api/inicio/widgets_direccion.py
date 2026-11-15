from datetime import timedelta

from django.db import connection
from django.db.models import Exists, OuterRef

from api.inicio.cache import memo_user
from api.inicio.registro import registrar
from api.inicio.utils import dinero, reverse_home
from api.inicio.widgets import Widget, WidgetData
from aula.models import CalificacionActividad
from campus.models import TicketAyuda, TicketRespuesta
from ventas.models import EdicionCurso

ALERTA_DANGER = 5


def _tone(n, danger=ALERTA_DANGER):
    if n >= danger:
        return "text-bg-danger"
    return "text-bg-warning"


def _kpis(user, hoy):
    def _load():
        inicio_mes = hoy.replace(day=1)
        limite = hoy - timedelta(days=7)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  (SELECT COALESCE(SUM(monto), 0) FROM tra_pago WHERE date(fecha_pago) >= %s AND estado = 'aplicado'),
                  (SELECT COUNT(*) FROM tra_venta WHERE fecha >= %s AND estado = 'confirmada'),
                  (SELECT COUNT(*) FROM tra_venta WHERE estado = 'confirmada' AND estado_pago IN ('pendiente', 'parcial')),
                  (SELECT COUNT(*) FROM tra_solicitud_baja WHERE estado = 'enviada'),
                  (SELECT COUNT(*) FROM tra_documento_expediente WHERE estado = 'en_revision'),
                  (SELECT COUNT(*) FROM campus_ticket_ayuda WHERE estado IN ('abierto', 'en_atencion')),
                  (SELECT COUNT(*) FROM cat_alumno WHERE estado = 'activo'),
                  (SELECT COUNT(*) FROM tra_acta_final a JOIN cat_periodo p ON a.periodo_id = p.id
                     WHERE a.estado = 'borrador' AND p.fecha_fin < %s AND p.cerrado = 0),
                  (SELECT COUNT(*) FROM solicitud_oferta WHERE date(creada_en) >= %s),
                  (SELECT COUNT(*) FROM campus_aviso_institucional WHERE publicado = 1 AND tipo = 'importante'
                     AND (vigencia_inicio IS NULL OR vigencia_inicio <= %s)
                     AND (vigencia_fin IS NULL OR vigencia_fin >= %s))
                """,
                [inicio_mes, inicio_mes, hoy, inicio_mes, hoy, hoy],
            )
            row = cursor.fetchone()
        pendientes = CalificacionActividad.objects.filter(entregado=True, calificacion__isnull=True)
        sin_nota = pendientes.count()
        viejas = pendientes.filter(fecha_entrega__lt=limite).count()
        grupos = EdicionCurso.objects.filter(activo=True, estado="en_curso").count()
        sin_respuesta = (
            TicketAyuda.objects.filter(estado__in=["abierto", "en_atencion"])
            .annotate(staff=Exists(TicketRespuesta.objects.filter(ticket=OuterRef("pk"), es_staff=True)))
            .filter(staff=False)
            .count()
        )
        return {
            "cobrado": row[0] if row else 0,
            "ventas_mes": row[1] if row else 0,
            "por_cobrar": row[2] if row else 0,
            "bajas": row[3] if row else 0,
            "expedientes": row[4] if row else 0,
            "tickets": row[5] if row else 0,
            "alumnos": row[6] if row else 0,
            "actas": row[7] if row else 0,
            "solicitudes": row[8] if row else 0,
            "avisos": row[9] if row else 0,
            "sin_nota": sin_nota,
            "viejas": viejas,
            "grupos": grupos,
            "sin_respuesta": sin_respuesta,
        }

    return memo_user(user, f"dir-kpis:{hoy}", _load)


def _ventas(user, hoy):
    k = _kpis(user, hoy)
    meses = (
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    )
    alerta = f"{k['por_cobrar']} folios por cobrar" if k["por_cobrar"] else ""
    return WidgetData(
        count=k["por_cobrar"],
        items=[],
        tipo="kpi",
        kpi=f"{dinero(k['cobrado'])} cobrados en {meses[hoy.month - 1]}",
        secundario=f"{k['ventas_mes']} ventas confirmadas del mes",
        alerta=alerta,
        alerta_tone=_tone(k["por_cobrar"]),
        cta_url=reverse_home("ventas_home", "direccion.ventas"),
        cta_label="Ir a Ventas",
    )


def _escolar(user, hoy):
    k = _kpis(user, hoy)
    tramites = k["bajas"] + k["expedientes"] + k["tickets"]
    alerta = f"{k['actas']} actas atrasadas" if k["actas"] else ""
    return WidgetData(
        count=tramites,
        items=[],
        tipo="kpi",
        kpi=f"{tramites} trámites abiertos",
        secundario=f"{k['alumnos']} alumnos activos",
        alerta=alerta,
        alerta_tone=_tone(k["actas"]),
        cta_url=reverse_home("inicio", "direccion.escolar", extra={"ctx": "escolar"}),
        cta_label="Ir a Control escolar",
    )


def _aula(user, hoy):
    k = _kpis(user, hoy)
    alerta = f"{k['viejas']} entregas con más de 7 días sin nota" if k["viejas"] else ""
    return WidgetData(
        count=k["sin_nota"],
        items=[],
        tipo="kpi",
        kpi=f"{k['sin_nota']} entregas sin calificar",
        secundario=f"{k['grupos']} grupos en curso",
        alerta=alerta,
        alerta_tone=_tone(k["viejas"]),
        cta_url=reverse_home("aula_dashboard", "direccion.aula"),
        cta_label="Ir a Aula",
    )


def _campus(user, hoy):
    k = _kpis(user, hoy)
    alerta = f"{k['sin_respuesta']} tickets sin respuesta" if k["sin_respuesta"] else ""
    return WidgetData(
        count=k["solicitudes"] + k["sin_respuesta"],
        items=[],
        tipo="kpi",
        kpi=f"{k['solicitudes']} solicitudes de cursos del mes",
        secundario=f"{k['avisos']} avisos importantes vigentes",
        alerta=alerta,
        alerta_tone=_tone(k["sin_respuesta"]),
        cta_url=reverse_home("ventas_solicitudes_oferta", "direccion.campus"),
        cta_label="Ir a Campus",
    )


registrar(Widget("direccion.ventas", "Ventas", "direccion", "ventas.panel", 10, "bi-cart3", _ventas))
registrar(Widget("direccion.escolar", "Control escolar", "direccion", "sii.panel", 20, "bi-building", _escolar))
registrar(Widget("direccion.aula", "Aula", "direccion", "aula.cursos", 30, "bi-journal-bookmark", _aula))
registrar(
    Widget("direccion.campus", "Campus", "direccion", "ventas.solicitudes_oferta", 40, "bi-mortarboard", _campus)
)
