from datetime import timedelta
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from api.inicio.cache import memo, solo_conteo
from api.inicio.registro import registrar
from api.inicio.utils import cola, dias_desde, dinero, formato_antiguedad, reverse_home, top5
from api.inicio.widgets import Item, Widget, WidgetData
from ventas.models import EdicionCurso, Pago, SolicitudOferta, Venta, VentaDetalle, Vendedor


def _ventas_con_saldo(qs):
    cero = Value(Decimal("0"), output_field=DecimalField(max_digits=19, decimal_places=4))
    linea = ExpressionWrapper(
        (Coalesce(F("precio_unitario"), F("id_producto__precio_unitario")) * F("cantidad"))
        - Coalesce(F("descuento"), cero),
        output_field=DecimalField(max_digits=19, decimal_places=4),
    )
    total_sq = (
        VentaDetalle.objects.filter(id_venta=OuterRef("pk"))
        .values("id_venta")
        .annotate(s=Sum(linea))
        .values("s")[:1]
    )
    pagado_sq = Pago.objects.filter(id_venta=OuterRef("pk")).values("id_venta").annotate(s=Sum("monto")).values("s")[:1]
    return qs.annotate(total_anotado=Coalesce(Subquery(total_sq), cero), pagado_anotado=Coalesce(Subquery(pagado_sq), cero))


def _pagos_qs():
    return _ventas_con_saldo(
        Venta.objects.filter(estado="confirmada", estado_pago__in=["pendiente", "parcial"]).select_related("id_cliente")
    ).order_by("registrado_en")


def _pagos(user, hoy):
    qs = _pagos_qs()
    request = getattr(user, "_inicio_request", None)
    count, filas = cola(qs, user)
    if request is not None:
        store = getattr(request, "_inicio_memo", None)
        if store is None:
            store = {}
            request._inicio_memo = store
        store.setdefault("pagos_pendientes", count)
    items = []
    for venta in filas:
        saldo = (venta.total_anotado or 0) - (venta.pagado_anotado or 0)
        cliente = venta.id_cliente
        items.append(
            Item(
                titulo=venta.folio or f"V-{venta.pk:06d}",
                meta=f"{cliente} · saldo {dinero(saldo)}",
                url=reverse_home("Pagos", "ventas.pagos", extra={"venta": venta.pk}),
                badge=venta.get_estado_pago_display(),
                badge_tone="text-bg-warning" if venta.estado_pago == "pendiente" else "text-bg-info",
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("Pagos", "ventas.pagos", extra={"estado_pago": "pendiente,parcial"}),
        cta_label="Registrar pago",
        ver_todos_url=reverse_home("Pagos", "ventas.pagos", extra={"estado_pago": "pendiente,parcial"}),
        mensaje_vacio="No hay pagos por confirmar",
    )


def _solicitudes(user, hoy):
    qs = (
        SolicitudOferta.objects.filter(estado="enviada")
        .select_related("alumno", "edicion__id_curso")
        .order_by("creada_en")
    )
    count, filas = cola(qs, user)
    items = []
    for sol in filas:
        curso = sol.edicion.id_curso.producto if sol.edicion_id else ""
        items.append(
            Item(
                titulo=str(sol.alumno),
                meta=f"{curso} · {sol.edicion.codigo_edicion} · {formato_antiguedad(dias_desde(sol.creada_en, hoy))}",
                url=reverse_home("ventas_solicitudes_oferta", "ventas.solicitudes", extra={"estado": "enviada"}),
            )
        )
    from sii.rbac import has_feature

    data = WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("ventas_solicitudes_oferta", "ventas.solicitudes", extra={"estado": "enviada"}),
        cta_label="Atender",
        ver_todos_url=reverse_home("ventas_solicitudes_oferta", "ventas.solicitudes", extra={"estado": "enviada"}),
        mensaje_vacio="No hay solicitudes pendientes",
    )
    if has_feature(user, "ventas.pos"):
        data.cta_secundario_url = reverse_home("Carrito", "ventas.solicitudes")
        data.cta_secundario_label = "Inscribir en POS"
    return data


def _ediciones(user, hoy):
    hasta = hoy + timedelta(days=14)
    qs = (
        EdicionCurso.objects.filter(activo=True, estado="programada", fecha_inicio__range=(hoy, hasta))
        .select_related("id_curso")
        .order_by("fecha_inicio")
    )
    count, filas = cola(qs, user)
    items = []
    for ed in filas:
        ocupado = int(ed.cupo_ocupado or 0)
        maximo = int(ed.cupo_maximo or 0)
        alerta = ""
        tone = "text-bg-light"
        if maximo and ocupado >= maximo:
            alerta = "llena"
            tone = "text-bg-danger"
        elif maximo and (ocupado / maximo) < 0.3:
            alerta = "cupo bajo"
            tone = "text-bg-warning"
        items.append(
            Item(
                titulo=ed.codigo_edicion,
                meta=f"{ed.id_curso.producto} · {ed.fecha_inicio} · {ocupado}/{maximo}",
                url=reverse_home("Ediciones", "ventas.ediciones"),
                badge=alerta or f"{ocupado}/{maximo}",
                badge_tone=tone,
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("Ediciones", "ventas.ediciones"),
        cta_label="Ver ediciones",
        mensaje_vacio="No hay ediciones por arrancar",
    )


def _mis_ventas_hoy(user, hoy):
    vendedor = Vendedor.para_usuario(user)
    if vendedor is None:
        return WidgetData(count=0, items=[], ocultar=True)
    qs = _ventas_con_saldo(Venta.objects.filter(id_vendedor=vendedor, fecha=hoy, estado="confirmada"))
    n = qs.count()
    items = []
    if n and not solo_conteo(user):
        monto = qs.aggregate(monto=Sum("total_anotado"))["monto"] or Decimal("0")
        items.append(
            Item(
                titulo=f"{n} ventas · {dinero(monto)}",
                meta="Confirmadas hoy",
                url=reverse_home("Ventas", "ventas.mis_ventas_hoy"),
            )
        )
    return WidgetData(
        count=n,
        items=items,
        cta_url=reverse_home("Carrito", "ventas.mis_ventas_hoy"),
        cta_label="Nueva venta",
        mensaje_vacio="Aún no registras ventas hoy",
    )


def _recientes(user, hoy):
    qs = _ventas_con_saldo(Venta.objects.select_related("id_cliente")).order_by("-registrado_en")
    filas = top5(qs, user)
    items = []
    for venta in filas:
        items.append(
            Item(
                titulo=venta.folio or f"V-{venta.pk:06d}",
                meta=f"{venta.id_cliente} · {dinero(venta.total_anotado)}",
                url=reverse_home("Ventas", "ventas.recientes"),
                badge=venta.get_estado_pago_display(),
                badge_tone="text-bg-warning" if venta.estado_pago == "pendiente" else "text-bg-light",
            )
        )
    count = len(filas) if filas else (0 if solo_conteo(user) else 0)
    if solo_conteo(user):
        count = 1 if qs.exists() else 0
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("Ventas", "ventas.recientes"),
        cta_label="Ver folios",
        mensaje_vacio="No hay folios recientes",
    )


registrar(Widget("ventas.pagos", "Pagos por confirmar", "ventas", "ventas.pagos", 10, "bi-credit-card", _pagos))
registrar(
    Widget(
        "ventas.solicitudes",
        "Solicitudes de cursos recomendados",
        "ventas",
        "ventas.solicitudes_oferta",
        20,
        "bi-inbox",
        _solicitudes,
    )
)
registrar(Widget("ventas.ediciones", "Ediciones por arrancar", "ventas", "ventas.ediciones", 30, "bi-calendar-event", _ediciones))
registrar(Widget("ventas.mis_ventas_hoy", "Mis ventas de hoy", "ventas", "ventas.folios", 40, "bi-receipt", _mis_ventas_hoy))
registrar(Widget("ventas.recientes", "Folios recientes", "ventas", "ventas.folios", 90, "bi-clock-history", _recientes))
