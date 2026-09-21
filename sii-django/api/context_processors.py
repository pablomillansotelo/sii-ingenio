from django.urls import reverse

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
    elif path.startswith("/sii") or path.startswith("/dashboard"):
        module = "sii"
        title = "SII"
    else:
        module = "inicio"
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
    features = frozenset()
    if user is not None and getattr(user, "is_authenticated", False):
        from sii.identity import modulos_permitidos
        from ventas.models import Venta

        permitidos = modulos_permitidos(user)
        features = features_de(user)
        display_name = (user.get_full_name() or user.get_username()).strip()
        if has_feature(user, "ventas.pagos"):
            pagos_pendientes = Venta.objects.filter(estado_pago="pendiente").count()

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
        for item in HOY_SHORTCUTS:
            if not visible_en_menu(user, item):
                continue
            badge = pagos_pendientes or None if item.get("badge") == "pagos" else None
            sidebar.append({
                "label": item["label"],
                "href": _url(item["url_name"]),
                "icon": item["icon"],
                "active": False,
                "badge": badge,
            })
    else:
        sidebar.extend(nav_items)

    en_pagos = path.startswith("/ventas/pagos")
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
        "ingenio_mostrar_cobro": bool(pagos_pendientes) and not en_pagos and has_feature(user, "ventas.pagos"),
    }
