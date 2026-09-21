"""Catálogo de features y candado por vista (RBAC Fase 0)."""
from functools import wraps

from django.core.exceptions import PermissionDenied

from sii.permissions import (
    GRUPO_ADMINISTRADOR,
    GRUPO_ALUMNO,
    GRUPO_DOCENTE,
    GRUPO_VENDEDOR,
)

ADMIN = GRUPO_ADMINISTRADOR
VENDEDOR = GRUPO_VENDEDOR
DOCENTE = GRUPO_DOCENTE
ALUMNO = GRUPO_ALUMNO

_SCOPE_RANK = {"all": 3, "assigned": 2, "own": 1}

FEATURES = {
    "ventas.panel": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.pos": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.folios": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.pagos": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.clientes": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.cursos": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.ediciones": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.vendedores": {"roles": {VENDEDOR, ADMIN}, "scopes": {VENDEDOR: "all", ADMIN: "all"}},
    "ventas.vendedores.write": {"roles": {ADMIN}, "scopes": {ADMIN: "all"}},
    "ventas.mis_compras": {"roles": {ALUMNO, ADMIN}, "scopes": {ALUMNO: "own", ADMIN: "all"}},
    "ventas.cliente.inscripcion_peek": {
        "roles": {VENDEDOR, ADMIN},
        "scopes": {VENDEDOR: "all", ADMIN: "all"},
    },
    "sii.panel": {
        "roles": {ADMIN, DOCENTE, ALUMNO},
        "scopes": {ADMIN: "all", DOCENTE: "assigned", ALUMNO: "own"},
    },
    "sii.alumnos": {
        "roles": {ADMIN, DOCENTE, ALUMNO},
        "scopes": {ADMIN: "all", DOCENTE: "assigned", ALUMNO: "own"},
    },
    "sii.alumnos.write": {"roles": {ADMIN}, "scopes": {ADMIN: "all"}},
    "sii.cursos": {
        "roles": {ADMIN, DOCENTE, ALUMNO},
        "scopes": {ADMIN: "all", DOCENTE: "assigned", ALUMNO: "own"},
    },
    "sii.cursos.write": {"roles": {ADMIN}, "scopes": {ADMIN: "all"}},
    "sii.periodos": {
        "roles": {ADMIN, DOCENTE, ALUMNO},
        "scopes": {ADMIN: "all", DOCENTE: "all", ALUMNO: "all"},
    },
    "sii.periodos.write": {"roles": {ADMIN}, "scopes": {ADMIN: "all"}},
    "sii.inscripciones": {
        "roles": {ADMIN, DOCENTE, ALUMNO},
        "scopes": {ADMIN: "all", DOCENTE: "assigned", ALUMNO: "own"},
    },
    "sii.inscripciones.write": {"roles": {ADMIN}, "scopes": {ADMIN: "all"}},
    "sii.docentes": {
        "roles": {ADMIN, DOCENTE},
        "scopes": {ADMIN: "all", DOCENTE: "own"},
    },
    "sii.docentes.write": {"roles": {ADMIN}, "scopes": {ADMIN: "all"}},
    "sii.kardex": {
        "roles": {ADMIN, DOCENTE, ALUMNO},
        "scopes": {ADMIN: "all", DOCENTE: "assigned", ALUMNO: "own"},
    },
    "sii.actas.final.write": {
        "roles": {ADMIN, DOCENTE},
        "scopes": {ADMIN: "all", DOCENTE: "assigned"},
    },
    "aula.cursos": {
        "roles": {ADMIN, DOCENTE, ALUMNO},
        "scopes": {ADMIN: "all", DOCENTE: "assigned", ALUMNO: "own"},
    },
    "aula.actividades": {
        "roles": {ADMIN, DOCENTE},
        "scopes": {ADMIN: "all", DOCENTE: "assigned"},
    },
    "aula.entregar": {"roles": {ALUMNO}, "scopes": {ALUMNO: "own"}},
    "aula.calificar": {
        "roles": {ADMIN, DOCENTE},
        "scopes": {ADMIN: "all", DOCENTE: "assigned"},
    },
    "aula.asignar_docente": {"roles": {ADMIN}, "scopes": {ADMIN: "all"}},
}

URL_FEATURES = {
    "ventas_home": ("ventas.panel", "ventas.mis_compras"),
    "Carrito": "ventas.pos",
    "ventas_carrito": "ventas.pos",
    "AddCarrito": "ventas.pos",
    "Ventas": "ventas.folios",
    "ventas_folios_alias": "ventas.folios",
    "EditVenta": "ventas.folios",
    "DeleteVenta": "ventas.folios",
    "Pagos": "ventas.pagos",
    "AddPago": "ventas.pagos",
    "EditPago": "ventas.pagos",
    "DeletePago": "ventas.pagos",
    "Clientes": "ventas.clientes",
    "AddCliente": "ventas.clientes",
    "EditCliente": "ventas.clientes",
    "DeleteCliente": "ventas.clientes",
    "Inventario": "ventas.cursos",
    "ventas_inventario_alias": "ventas.cursos",
    "AddProducto": "ventas.cursos",
    "EditProducto": "ventas.cursos",
    "DeleteProducto": "ventas.cursos",
    "Ediciones": "ventas.ediciones",
    "AddEdicion": "ventas.ediciones",
    "EditEdicion": "ventas.ediciones",
    "DeleteEdicion": "ventas.ediciones",
    "Vendedores": "ventas.vendedores",
    "AddVendedor": "ventas.vendedores.write",
    "EditVendedor": "ventas.vendedores.write",
    "DeleteVendedor": "ventas.vendedores.write",
    "mis_compras": "ventas.mis_compras",
    "sii_home": "sii.panel",
    "sii_alumnos": "sii.alumnos",
    "sii_alumno_crear": "sii.alumnos.write",
    "sii_alumno_editar": "sii.alumnos.write",
    "sii_cursos": "sii.cursos",
    "sii_curso_crear": "sii.cursos.write",
    "sii_curso_editar": "sii.cursos.write",
    "sii_periodos": "sii.periodos",
    "sii_periodo_crear": "sii.periodos.write",
    "sii_periodo_editar": "sii.periodos.write",
    "sii_inscripciones": "sii.inscripciones",
    "sii_inscripcion_crear": "sii.inscripciones.write",
    "sii_inscripcion_baja": "sii.inscripciones.write",
    "sii_inscripcion_reintento": "sii.inscripciones.write",
    "sii_docentes": "sii.docentes",
    "sii_docente_crear": "sii.docentes.write",
    "sii_docente_editar": "sii.docentes.write",
    "sii_asignacion_crear": "sii.docentes.write",
    "sii_asignacion_quitar": "sii.docentes.write",
    "aula_dashboard": "aula.cursos",
    "aula_curso": "aula.cursos",
    "aula_kardex": "sii.kardex",
    "aula_actividad_nueva": "aula.actividades",
    "aula_actividad_editar": "aula.actividades",
    "aula_entregar": "aula.entregar",
    "aula_calificar": "aula.calificar",
    "aula_guardar_calificacion": "aula.calificar",
    "aula_asignar_docente": "aula.asignar_docente",
}

NAV = {
    "ventas": [
        {"label": "Panel", "url_name": "ventas_home", "icon": "bi-speedometer2", "feature": "ventas.panel"},
        {"label": "Punto de venta", "url_name": "Carrito", "icon": "bi-bag-plus", "feature": "ventas.pos"},
        {"label": "Folios", "url_name": "Ventas", "icon": "bi-receipt", "feature": "ventas.folios"},
        {"label": "Pagos", "url_name": "Pagos", "icon": "bi-credit-card", "feature": "ventas.pagos"},
        {"label": "Mis compras", "url_name": "mis_compras", "icon": "bi-wallet2", "feature": "ventas.mis_compras"},
        {"label": "Clientes", "url_name": "Clientes", "icon": "bi-people", "feature": "ventas.clientes"},
        {"label": "Cursos", "url_name": "Inventario", "icon": "bi-collection", "feature": "ventas.cursos"},
        {"label": "Ediciones", "url_name": "Ediciones", "icon": "bi-calendar-event", "feature": "ventas.ediciones"},
        {"label": "Vendedores", "url_name": "Vendedores", "icon": "bi-person-badge", "feature": "ventas.vendedores"},
    ],
    "sii": [
        {"label": "Panel", "url_name": "sii_home", "icon": "bi-speedometer2", "feature": "sii.panel"},
        {"label": "Alumnos", "url_name": "sii_alumnos", "icon": "bi-people", "feature": "sii.alumnos", "hide_if_own": True},
        {"label": "Cursos", "url_name": "sii_cursos", "icon": "bi-journal-text", "feature": "sii.cursos", "hide_if_own": True},
        {
            "label": "Periodos",
            "url_name": "sii_periodos",
            "icon": "bi-calendar3",
            "feature": "sii.periodos",
            "nav_roles": {ADMIN, DOCENTE},
        },
        {"label": "Inscripciones", "url_name": "sii_inscripciones", "icon": "bi-clipboard-check", "feature": "sii.inscripciones", "hide_if_own": True},
        {"label": "Docentes", "url_name": "sii_docentes", "icon": "bi-person-video3", "feature": "sii.docentes", "hide_if_own": True},
    ],
    "aula": [
        {"label": "Mis cursos", "url_name": "aula_dashboard", "icon": "bi-grid", "feature": "aula.cursos"},
        {"label": "Kardex", "url_name": "aula_kardex", "icon": "bi-table", "feature": "sii.kardex"},
    ],
}

MODULE_LANDINGS = {
    "ventas": (("ventas_home", "ventas.panel"), ("mis_compras", "ventas.mis_compras")),
    "sii": (("sii_home", "sii.panel"),),
    "aula": (("aula_dashboard", "aula.cursos"),),
}

HOY_SHORTCUTS = [
    {"label": "Nueva venta", "url_name": "Carrito", "icon": "bi-bag-plus", "feature": "ventas.pos"},
    {
        "label": "Registrar pago",
        "url_name": "Pagos",
        "icon": "bi-credit-card",
        "feature": "ventas.pagos",
        "badge": "pagos",
    },
    {
        "label": "Mis compras",
        "url_name": "mis_compras",
        "icon": "bi-wallet2",
        "feature": "ventas.mis_compras",
        "skip_if": "ventas.pos",
    },
    {
        "label": "Inscripciones",
        "url_name": "sii_inscripciones",
        "icon": "bi-clipboard-check",
        "feature": "sii.inscripciones",
        "hide_if_own": True,
    },
    {"label": "Aula", "url_name": "aula_dashboard", "icon": "bi-journal-bookmark", "feature": "aula.cursos"},
]


def _normalizar_codigos(codigo_o_codigos):
    if codigo_o_codigos is None:
        return ()
    if isinstance(codigo_o_codigos, str):
        return (codigo_o_codigos,)
    return tuple(codigo_o_codigos)


def features_de(user):
    if user is None or not getattr(user, "is_authenticated", False):
        return frozenset()
    cached = getattr(user, "_ingenio_features", None)
    if cached is not None:
        return cached
    if user.is_superuser:
        feats = frozenset(FEATURES)
        user._ingenio_features = feats
        return feats
    from sii.identity import roles_inferidos

    roles = roles_inferidos(user)
    feats = frozenset(codigo for codigo, spec in FEATURES.items() if roles & spec["roles"])
    user._ingenio_features = feats
    return feats


def has_feature(user, codigo):
    return codigo in features_de(user)


def has_any_feature(user, codigos):
    return any(has_feature(user, codigo) for codigo in _normalizar_codigos(codigos))


def scope_for(user, codigo):
    if not has_feature(user, codigo):
        return None
    if user is not None and getattr(user, "is_superuser", False):
        return "all"
    spec = FEATURES[codigo]
    from sii.identity import roles_inferidos

    mejor = None
    mejor_rango = 0
    for rol in roles_inferidos(user):
        if rol not in spec["roles"]:
            continue
        alcance = spec.get("scopes", {}).get(rol, "all")
        rango = _SCOPE_RANK.get(alcance, 0)
        if rango > mejor_rango:
            mejor, mejor_rango = alcance, rango
    return mejor


def visible_en_menu(user, item):
    feature = item.get("feature")
    if feature and not has_feature(user, feature):
        return False
    skip = item.get("skip_if")
    if skip and has_feature(user, skip):
        return False
    if item.get("hide_if_own") and feature and scope_for(user, feature) == "own":
        return False
    nav_roles = item.get("nav_roles")
    if nav_roles:
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        if not user.is_superuser:
            from sii.identity import roles_inferidos

            if not (roles_inferidos(user) & nav_roles):
                return False
    return True


def landing_modulo(user, modulo):
    for url_name, feature in MODULE_LANDINGS.get(modulo, ()):
        if has_feature(user, feature):
            return url_name
    return None


def dominios_permitidos(user):
    return {modulo for modulo in MODULE_LANDINGS if landing_modulo(user, modulo)}


def feature_para_url(url_name):
    return URL_FEATURES.get(url_name)


def requiere_feature(*codigos):
    requeridas = _normalizar_codigos(codigos)

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_any_feature(request.user, requeridas):
                raise PermissionDenied("No tienes acceso a esa función.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
