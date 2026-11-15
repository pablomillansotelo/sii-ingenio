from sii.identity import docente_para_usuario, es_administrador
from sii.rbac import has_feature
from ventas.models import Vendedor

CONTEXTOS = {
    "escolar": {"clave": "escolar", "label": "Control escolar", "icono": "bi-building"},
    "ventas": {"clave": "ventas", "label": "Ventas", "icono": "bi-cart3"},
    "docente": {"clave": "docente", "label": "Docencia", "icono": "bi-journal-bookmark"},
    "direccion": {"clave": "direccion", "label": "Dirección", "icono": "bi-graph-up"},
}

PRIORIDAD_DEFAULT = ["escolar", "ventas", "docente", "direccion"]
SESSION_KEY = "inicio_ctx"
FEATURES_ESCOLAR = ("sii.bajas", "sii.expediente", "sii.ayuda", "sii.aceptacion")


def contextos_disponibles(user) -> list[dict]:
    disponibles = []
    if es_administrador(user) and any(has_feature(user, codigo) for codigo in FEATURES_ESCOLAR):
        disponibles.append(CONTEXTOS["escolar"])
    if has_feature(user, "ventas.panel"):
        disponibles.append(CONTEXTOS["ventas"])
    if docente_para_usuario(user) is not None:
        disponibles.append(CONTEXTOS["docente"])
    if es_administrador(user):
        disponibles.append(CONTEXTOS["direccion"])
    return disponibles


def _claves(user) -> list[str]:
    return [item["clave"] for item in contextos_disponibles(user)]


def _es_superusuario_sin_fichas(user) -> bool:
    if user is None or not getattr(user, "is_superuser", False):
        return False
    if Vendedor.para_usuario(user) is not None:
        return False
    if docente_para_usuario(user) is not None:
        return False
    return True


def contexto_por_defecto(user) -> str | None:
    claves = _claves(user)
    if not claves:
        return None
    if _es_superusuario_sin_fichas(user) and "direccion" in claves:
        return "direccion"
    for clave in PRIORIDAD_DEFAULT:
        if clave in claves:
            return clave
    return claves[0]


def contexto_activo(request) -> str | None:
    user = getattr(request, "user", None)
    claves = _claves(user)
    if not claves:
        request.inicio_ctx = None
        return None

    pedido = (request.GET.get("ctx") or "").strip()
    if pedido in claves:
        request.session[SESSION_KEY] = pedido
        request.inicio_ctx = pedido
        return pedido

    sesion = request.session.get(SESSION_KEY)
    if sesion in claves:
        request.inicio_ctx = sesion
        return sesion

    elegido = contexto_por_defecto(user)
    if elegido:
        request.session[SESSION_KEY] = elegido
    request.inicio_ctx = elegido
    return elegido
