from django.urls import reverse

from api.inicio.cache import memo
from api.inicio.contextos import CONTEXTOS
from sii.rbac import (
    HOY_SHORTCUTS,
    NAV,
    features_de,
    has_feature,
    landing_modulo,
    visible_en_menu,
)


def ingenio_shell(request):
    path = request.path or "/"
    match = getattr(request, "resolver_match", None)
    current_name = getattr(match, "url_name", None) if match else None

    if path.startswith("/ventas"):
        module = "ventas"
        title = "Ventas"
    elif path.startswith("/aula"):
        module = "aula"
        title = "Aula"
    elif path.startswith("/campus"):
        module = "campus"
        title = "Campus"
    elif path.startswith("/sii") or path.startswith("/dashboard"):
        module = "sii"
        title = "SII"
    else:
        module = "inicio"
        ctx = getattr(request, "inicio_ctx", None)
        if ctx and ctx in CONTEXTOS:
            title = f"Hoy · {CONTEXTOS[ctx]['label']}"
        else:
            title = "Hoy"

    catalogo = [
        {"key": "ventas", "label": "Ventas", "icon": "bi-cart3"},
        {"key": "sii", "label": "SII", "icon": "bi-building"},
        {"key": "aula", "label": "Aula", "icon": "bi-journal-bookmark"},
    ]

    def _url(name):
        try:
            return reverse(name)
        except Exception:
            return "#"

    user = getattr(request, "user", None)
    permitidos = set()
    display_name = ""
    pagos_pendientes = 0
    pendientes_calificar = 0
    features = frozenset()
    if user is not None and getattr(user, "is_authenticated", False):
        from sii.identity import modulos_permitidos
        from ventas.models import Venta

        permitidos = modulos_permitidos(user)
        features = features_de(user)
        display_name = (user.get_full_name() or user.get_username()).strip()

    modules = []
    for item in catalogo:
        landing = landing_modulo(user, item["key"]) if user else None
        if not landing:
            continue
        modules.append({
            **item,
            "url_name": landing,
            "href": _url(landing),
            "active": item["key"] == module,
        })

    nav_items = []
    if module != "inicio" and module in permitidos:
        for item in NAV.get(module, []):
            if not visible_en_menu(user, item):
                continue
            href = _url(item["url_name"])
            nav_items.append({
                **item,
                "href": href,
                "active": current_name == item["url_name"],
            })

    def _badge_de(item):
        kind = item.get("badge")
        if kind == "pagos":
            if not pagos_pendientes and has_feature(user, "ventas.pagos"):
                from ventas.models import Venta

                nonlocal_pagos = memo(
                    request,
                    "pagos_pendientes",
                    lambda: Venta.objects.filter(
                        estado="confirmada", estado_pago__in=["pendiente", "parcial"]
                    ).count(),
                )
                return nonlocal_pagos or None
            return pagos_pendientes or None
        if kind == "calificar":
            if not pendientes_calificar and has_feature(user, "aula.calificar"):
                from aula.services import entregas_pendientes_qs

                n = memo(request, "pendientes_calificar", lambda: entregas_pendientes_qs(user).count())
                return n or None
            return pendientes_calificar or None
        return None

    sidebar = [
        {
            "label": "Hoy",
            "href": _url("inicio"),
            "icon": "bi-house",
            "active": module == "inicio",
            "badge": None,
        }
    ]
    if module == "inicio":
        ctx_activo = getattr(request, "inicio_ctx", None)
        for item in HOY_SHORTCUTS:
            if item.get("contexto") and ctx_activo and item["contexto"] != ctx_activo:
                continue
            if not visible_en_menu(user, item):
                continue
            sidebar.append({
                "label": item["label"],
                "href": _url(item["url_name"]),
                "icon": item["icon"],
                "active": False,
                "badge": _badge_de(item),
            })
    else:
        for item in nav_items:
            sidebar.append({**item, "badge": _badge_de(item)})

    en_pagos = path.startswith("/ventas/pagos")
    memo_store = getattr(request, "_inicio_memo", {}) or {}
    pagos_pendientes = memo_store.get("pagos_pendientes", pagos_pendientes) or pagos_pendientes
    pendientes_calificar = memo_store.get("pendientes_calificar", pendientes_calificar) or pendientes_calificar
    return {
        "ingenio_module": module,
        "ingenio_title": title,
        "ingenio_modules": modules,
        "ingenio_nav": nav_items,
        "ingenio_sidebar": sidebar,
        "ingenio_display_name": display_name,
        "ingenio_modulos_permitidos": permitidos,
        "ingenio_features": features,
        "ingenio_pagos_pendientes": pagos_pendientes,
        "ingenio_pendientes_calificar": pendientes_calificar,
        "ingenio_mostrar_cobro": bool(pagos_pendientes) and not en_pagos and has_feature(user, "ventas.pagos"),
    }
