from django.urls import reverse


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
        title = "Ingenio"

    catalogo = [
        {"key": "ventas", "label": "Ventas", "url_name": "ventas_home", "icon": "bi-cart3"},
        {"key": "sii", "label": "SII", "url_name": "sii_home", "icon": "bi-building"},
        {"key": "aula", "label": "Aula", "url_name": "aula_dashboard", "icon": "bi-journal-bookmark"},
    ]

    nav = {
        "inicio": [
            {"label": "Inicio", "url_name": "inicio", "icon": "bi-house"},
        ],
        "ventas": [
            {"label": "Panel", "url_name": "ventas_home", "icon": "bi-speedometer2"},
            {"label": "Punto de venta", "url_name": "Carrito", "icon": "bi-bag-plus"},
            {"label": "Folios", "url_name": "Ventas", "icon": "bi-receipt"},
            {"label": "Pagos", "url_name": "Pagos", "icon": "bi-credit-card"},
            {"label": "Clientes", "url_name": "Clientes", "icon": "bi-people"},
            {"label": "Cursos", "url_name": "Inventario", "icon": "bi-collection"},
            {"label": "Ediciones", "url_name": "Ediciones", "icon": "bi-calendar-event"},
            {"label": "Vendedores", "url_name": "Vendedores", "icon": "bi-person-badge"},
        ],
        "sii": [
            {"label": "Panel", "url_name": "sii_home", "icon": "bi-speedometer2"},
            {"label": "Alumnos", "url_name": "sii_alumnos", "icon": "bi-people"},
            {"label": "Cursos", "url_name": "sii_cursos", "icon": "bi-journal-text"},
            {"label": "Periodos", "url_name": "sii_periodos", "icon": "bi-calendar3"},
            {"label": "Inscripciones", "url_name": "sii_inscripciones", "icon": "bi-clipboard-check"},
            {"label": "Docentes", "url_name": "sii_docentes", "icon": "bi-person-video3"},
        ],
        "aula": [
            {"label": "Mis cursos", "url_name": "aula_dashboard", "icon": "bi-grid"},
            {"label": "Kardex", "url_name": "aula_kardex", "icon": "bi-table"},
        ],
    }

    def _url(name):
        try:
            return reverse(name)
        except Exception:
            return "#"

    user = getattr(request, "user", None)
    permitidos = set()
    display_name = ""
    if user is not None and getattr(user, "is_authenticated", False):
        from sii.identity import modulos_permitidos

        permitidos = modulos_permitidos(user)
        display_name = (user.get_full_name() or user.get_username()).strip()

    modules = []
    for item in catalogo:
        if item["key"] not in permitidos:
            continue
        modules.append({
            **item,
            "href": _url(item["url_name"]),
            "active": item["key"] == module,
        })

    nav_items = []
    if module != "inicio" and module in permitidos:
        for item in nav.get(module, []):
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
        }
    ]
    if module == "inicio":
        sidebar.extend(modules)
    else:
        sidebar.extend(nav_items)

    return {
        "ingenio_module": module,
        "ingenio_title": title,
        "ingenio_modules": modules,
        "ingenio_nav": nav_items,
        "ingenio_sidebar": sidebar,
        "ingenio_display_name": display_name,
        "ingenio_modulos_permitidos": permitidos,
    }
