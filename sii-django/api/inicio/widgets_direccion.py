from datetime import timedelta

from django.db.models import Count, Exists, OuterRef, Q, Sum

from api.inicio.cache import memo_user
from api.inicio.registro import registrar
from api.inicio.utils import dinero, reverse_home
from api.inicio.widgets import Widget, WidgetData
from aula.models import CalificacionActividad
from campus.models import AvisoInstitucional, TicketAyuda, TicketRespuesta
from sii.models import ActaFinal, Alumno, DocumentoExpediente, SolicitudBaja
from ventas.models import EdicionCurso, Pago, SolicitudOferta, Venta

ALERTA_DANGER = 5


def _tone(n, danger=ALERTA_DANGER):
    if n >= danger:
        return "text-bg-danger"
    return "text-bg-warning"


def _kpis(user, hoy):
    def _load():
        inicio_mes = hoy.replace(day=1)
        limite = hoy - timedelta(days=7)
        cobrado = (
            Pago.objects.filter(estado="aplicado", fecha_pago__date__gte=inicio_mes).aggregate(total=Sum("monto"))[
                "total"
            ]
            or 0
        )
        ventas = Venta.objects.aggregate(
            mes=Count("pk", filter=Q(fecha__gte=inicio_mes, estado="confirmada")),
            por_cobrar=Count(
                "pk",
                filter=Q(estado="confirmada", estado_pago__in=["pendiente", "parcial"]),
            ),
        )
        tickets = (
            TicketAyuda.objects.filter(estado__in=["abierto", "en_atencion"])
            .annotate(staff=Exists(TicketRespuesta.objects.filter(ticket=OuterRef("pk"), es_staff=True)))
            .aggregate(
                abiertos=Count("pk"),
                sin_respuesta=Count("pk", filter=Q(staff=False)),
            )
        )
        notas = CalificacionActividad.objects.filter(entregado=True, calificacion__isnull=True).aggregate(
            sin_nota=Count("pk"),
            viejas=Count("pk", filter=Q(fecha_entrega__lt=limite)),
        )
        avisos = AvisoInstitucional.objects.filter(
            publicado=True,
            tipo=AvisoInstitucional.TIPO_IMPORTANTE,
        ).filter(
            Q(vigencia_inicio__isnull=True) | Q(vigencia_inicio__lte=hoy),
            Q(vigencia_fin__isnull=True) | Q(vigencia_fin__gte=hoy),
        )
        return {
            "cobrado": cobrado or 0,
            "ventas_mes": ventas["mes"],
            "por_cobrar": ventas["por_cobrar"],
            "bajas": SolicitudBaja.objects.filter(estado="enviada").count(),
            "expedientes": DocumentoExpediente.objects.filter(estado="en_revision").count(),
            "tickets": tickets["abiertos"],
            "alumnos": Alumno.objects.filter(estado="activo").count(),
            "actas": ActaFinal.objects.filter(
                estado="borrador",
                periodo__fecha_fin__lt=hoy,
                periodo__cerrado=False,
            ).count(),
            "solicitudes": SolicitudOferta.objects.filter(creada_en__date__gte=inicio_mes).count(),
            "avisos": avisos.count(),
            "sin_nota": notas["sin_nota"],
            "viejas": notas["viejas"],
            "grupos": EdicionCurso.objects.filter(activo=True, estado="en_curso").count(),
            "sin_respuesta": tickets["sin_respuesta"],
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
