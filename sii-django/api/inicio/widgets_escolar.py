from datetime import timedelta

from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Q, When
from api.inicio.registro import registrar
from api.inicio.utils import cola, dias_desde, formato_antiguedad, reverse_home, tono_por_antiguedad
from api.inicio.widgets import Item, Widget, WidgetData
from campus.models import TicketAyuda, TicketRespuesta
from campus.services.mensajes import hilos_no_leidos_qs
from sii.models import ActaFinal, AceptacionCarga, DocumentoExpediente, Inscripcion, Periodo, SolicitudBaja
from sii.rbac import scope_for


def _bajas(user, hoy):
    qs = (
        SolicitudBaja.objects.filter(estado="enviada")
        .select_related("alumno", "inscripcion__curso")
        .order_by("creada_en")
    )
    count, filas = cola(qs, user)
    items = []
    for sol in filas:
        dias = dias_desde(sol.creada_en, hoy)
        curso = sol.inscripcion.curso.nombre if sol.inscripcion_id else ""
        motivo = (sol.motivo or "")[:80]
        items.append(
            Item(
                titulo=str(sol.alumno),
                meta=f"{curso} · {motivo} · {formato_antiguedad(dias)}".strip(" ·"),
                url=reverse_home("sii_solicitudes_baja", "escolar.bajas", extra={"estado": "enviada"}),
                badge=formato_antiguedad(dias),
                badge_tone=tono_por_antiguedad(dias),
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_solicitudes_baja", "escolar.bajas", extra={"estado": "enviada"}),
        cta_label="Resolver",
        ver_todos_url=reverse_home("sii_solicitudes_baja", "escolar.bajas", extra={"estado": "enviada"}),
        mensaje_vacio="No hay bajas por resolver",
    )


def _expediente(user, hoy):
    qs = DocumentoExpediente.objects.filter(estado="en_revision").select_related("alumno").order_by("subido_en")
    count, filas = cola(qs, user)
    items = []
    for doc in filas:
        dias = dias_desde(doc.subido_en, hoy)
        items.append(
            Item(
                titulo=str(doc.alumno),
                meta=f"{doc.get_tipo_display()} · {formato_antiguedad(dias)}",
                url=reverse_home("sii_expediente", "escolar.expediente", extra={"estado": "en_revision"}),
                badge=formato_antiguedad(dias),
                badge_tone=tono_por_antiguedad(dias),
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_expediente", "escolar.expediente", extra={"estado": "en_revision"}),
        cta_label="Revisar",
        ver_todos_url=reverse_home("sii_expediente", "escolar.expediente", extra={"estado": "en_revision"}),
        mensaje_vacio="No hay expedientes por validar",
    )


def _ayuda(user, hoy):
    qs = (
        TicketAyuda.objects.filter(estado__in=["abierto", "en_atencion"])
        .select_related("alumno")
        .annotate(
            sin_respuesta=~Exists(TicketRespuesta.objects.filter(ticket=OuterRef("pk"), es_staff=True)),
            orden_estado=Case(When(estado="abierto", then=0), default=1, output_field=IntegerField()),
        )
        .order_by("orden_estado", "creado_en")
    )
    count, filas = cola(qs, user)
    items = []
    for ticket in filas:
        badge = "Sin respuesta" if ticket.sin_respuesta else ticket.get_estado_display()
        tone = "text-bg-danger" if ticket.sin_respuesta else "text-bg-warning"
        items.append(
            Item(
                titulo=ticket.folio or f"AYU-{ticket.pk}",
                meta=f"{ticket.asunto} · {ticket.get_categoria_display()} · {ticket.get_estado_display()}",
                url=reverse_home("sii_ayuda_detalle", "escolar.ayuda", args=[ticket.pk]),
                badge=badge,
                badge_tone=tone,
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_ayuda", "escolar.ayuda", extra={"estado": "abierto,en_atencion"}),
        cta_label="Responder",
        ver_todos_url=reverse_home("sii_ayuda", "escolar.ayuda", extra={"estado": "abierto,en_atencion"}),
        mensaje_vacio="No hay tickets abiertos",
    )


def _mensajes(user, hoy):
    qs = hilos_no_leidos_qs(user, para_control=True)
    count, filas = cola(qs, user)
    items = []
    for hilo in filas:
        items.append(
            Item(
                titulo=hilo.asunto,
                meta=formato_antiguedad(dias_desde(hilo.creado_en, hoy)),
                url=reverse_home("sii_hilo", "escolar.mensajes", args=[hilo.pk]),
                badge="Sin leer",
                badge_tone="text-bg-warning",
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_mensajes", "escolar.mensajes"),
        cta_label="Abrir",
        ver_todos_url=reverse_home("sii_mensajes", "escolar.mensajes"),
        mensaje_vacio="No hay mensajes sin leer",
    )


def _aceptacion(user, hoy):
    periodo_ids = list(
        Periodo.objects.filter(
            ventana_aceptacion_inicio__lte=hoy,
            ventana_aceptacion_fin__gte=hoy,
        ).values_list("pk", flat=True)
    )
    if not periodo_ids:
        return WidgetData(count=0, items=[], ocultar=True)
    agg = Inscripcion.objects.filter(estado="activo", periodo_id__in=periodo_ids).aggregate(
        faltan=Count("id", filter=Q(aceptacion__isnull=True)),
        cambios=Count("id", filter=Q(aceptacion__estado=AceptacionCarga.ESTADO_CAMBIO)),
    )
    faltan = agg["faltan"] or 0
    cambios = agg["cambios"] or 0
    count = faltan + cambios
    meta = f"{faltan} faltan por confirmar · {cambios} pidió cambio" if cambios != 1 else f"{faltan} faltan por confirmar · 1 pidió cambio"
    items = []
    if count and not getattr(user, "_inicio_solo_conteo", False):
        items.append(
            Item(
                titulo="Aceptación de materias",
                meta=meta,
                url=reverse_home("sii_aceptaciones", "escolar.aceptacion", extra={"pendiente": "1"}),
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_aceptaciones", "escolar.aceptacion", extra={"pendiente": "1"}),
        cta_label="Ver pendientes",
        mensaje_vacio="Nadie espera confirmación de carga",
    )


def _inscripciones(user, hoy):
    if scope_for(user, "sii.inscripciones") != "all":
        return WidgetData(count=0, items=[], ocultar=True)
    desde = hoy - timedelta(days=7)
    qs = (
        Inscripcion.objects.filter(fecha_inscripcion__gte=desde)
        .select_related("alumno", "curso", "periodo")
        .order_by("-fecha_inscripcion")
    )
    count, filas = cola(qs, user)
    items = []
    for ins in filas:
        alerta = "" if ins.puede_cursar else " · sin acceso a aula"
        items.append(
            Item(
                titulo=str(ins.alumno),
                meta=f"{ins.curso} · {ins.periodo}{alerta}",
                url=reverse_home("sii_inscripciones", "escolar.inscripciones"),
                badge=None if ins.puede_cursar else "Sin acceso",
                badge_tone=None if ins.puede_cursar else "text-bg-warning",
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_inscripciones", "escolar.inscripciones"),
        cta_label="Ver inscripciones",
        ver_todos_url=reverse_home("sii_inscripciones", "escolar.inscripciones"),
        mensaje_vacio="No hay inscripciones nuevas",
    )


def _actas(user, hoy):
    qs = (
        ActaFinal.objects.filter(estado="borrador", periodo__fecha_fin__lt=hoy, periodo__cerrado=False)
        .select_related("curso", "periodo")
        .order_by("periodo__fecha_fin")
    )
    count, filas = cola(qs, user)
    items = []
    for acta in filas:
        items.append(
            Item(
                titulo=f"{acta.curso} · {acta.periodo}",
                meta="Borrador · periodo terminado",
                url=reverse_home("sii_acta_detalle", "escolar.actas", args=[acta.pk]),
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_actas", "escolar.actas"),
        cta_label="Abrir acta",
        ver_todos_url=reverse_home("sii_actas", "escolar.actas"),
        mensaje_vacio="No hay actas por publicar",
    )


registrar(Widget("escolar.bajas", "Bajas por resolver", "escolar", "sii.bajas", 10, "bi-person-dash", _bajas))
registrar(Widget("escolar.expediente", "Expedientes por validar", "escolar", "sii.expediente", 20, "bi-folder2-open", _expediente))
registrar(Widget("escolar.ayuda", "Mesa de ayuda", "escolar", "sii.ayuda", 30, "bi-life-preserver", _ayuda))
registrar(Widget("escolar.mensajes", "Mensajes a control escolar sin leer", "escolar", "sii.mensajes", 40, "bi-chat-dots", _mensajes))
registrar(Widget("escolar.aceptacion", "Aceptación de materias", "escolar", "sii.aceptacion", 50, "bi-check2-square", _aceptacion))
registrar(
    Widget(
        "escolar.inscripciones",
        "Inscripciones nuevas",
        "escolar",
        "sii.inscripciones",
        60,
        "bi-person-plus",
        _inscripciones,
        scope="all",
    )
)
registrar(Widget("escolar.actas", "Actas por publicar", "escolar", "sii.actas", 70, "bi-journal-check", _actas))
