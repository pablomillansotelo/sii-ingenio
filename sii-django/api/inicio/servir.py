import logging

from django.utils import timezone

from api.inicio.badges import contar_contexto  # noqa: F401
from api.inicio.registro import widgets_para
from api.inicio.widgets import WidgetData

logger = logging.getLogger("api.inicio")


def _cargar(widget, user, hoy):
    try:
        data = widget.cargar(user, hoy)
    except Exception:
        logger.exception("No se pudo cargar el widget %s", widget.clave)
        return WidgetData(
            count=0,
            items=[],
            mensaje_vacio="No pudimos cargar esto",
            severidad="error",
        )
    return data


def cargar_widgets(user, contexto, hoy=None):
    hoy = hoy or timezone.localdate()
    cargados = []
    for widget in widgets_para(user, contexto):
        data = _cargar(widget, user, hoy)
        if data is None or getattr(data, "ocultar", False):
            continue
        items = list(data.items or [])
        if len(items) > 5:
            data.items = items[:5]
        cargados.append((widget, data))
    cargados.sort(key=lambda par: (0 if par[1].count else 1, par[0].prioridad, -(par[1].count or 0)))
    return cargados


# contar_contexto se implementa en badges.py (1 query por pestaña inactiva).
