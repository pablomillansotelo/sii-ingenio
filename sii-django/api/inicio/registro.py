from sii.rbac import has_feature, scope_for

from api.inicio.widgets import Widget

REGISTRO: dict[str, list[Widget]] = {
    "escolar": [],
    "ventas": [],
    "docente": [],
    "direccion": [],
}


def registrar(widget: Widget) -> Widget:
    lista = REGISTRO.setdefault(widget.contexto, [])
    lista[:] = [item for item in lista if item.clave != widget.clave]
    lista.append(widget)
    lista.sort(key=lambda item: item.prioridad)
    return widget


def widgets_para(user, contexto: str) -> list[Widget]:
    resultado = []
    for widget in REGISTRO.get(contexto, []):
        if widget.feature and not has_feature(user, widget.feature):
            continue
        if widget.cta_feature and not has_feature(user, widget.cta_feature):
            continue
        if widget.scope and scope_for(user, widget.feature) != widget.scope:
            continue
        resultado.append(widget)
    return resultado
