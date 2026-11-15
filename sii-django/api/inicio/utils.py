from datetime import date, datetime

from api.inicio.cache import solo_conteo
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.urls import reverse
from django.utils import timezone


def dias_desde(dt, hoy=None):
    hoy = hoy or timezone.localdate()
    if dt is None:
        return 0
    if isinstance(dt, datetime):
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt).date()
        else:
            dt = dt.date()
    elif not isinstance(dt, date):
        return 0
    return max(0, (hoy - dt).days)


def tono_por_antiguedad(dias):
    if dias > 7:
        return "text-bg-danger"
    if dias >= 3:
        return "text-bg-warning"
    return "text-bg-light"


def formato_antiguedad(dias):
    if dias <= 0:
        return "hoy"
    if dias == 1:
        return "hace 1 día"
    return f"hace {dias} días"


def with_from_home(url, clave, extra=None):
    parts = urlsplit(url or "")
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["from"] = "home"
    query["w"] = clave
    if extra:
        for key, value in extra.items():
            if value is None:
                continue
            query[key] = value
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))


def reverse_home(name, clave, args=None, extra=None):
    url = reverse(name, args=args or ())
    return with_from_home(url, clave, extra=extra)


def cola(qs, user):
    """Count + top 5 en una query (Window) o solo Count si es badge."""
    if solo_conteo(user):
        return qs.count(), []
    from django.db.models import Count, Window

    try:
        filas = list(qs.annotate(_cola_total=Window(expression=Count("pk")))[:5])
        total = int(getattr(filas[0], "_cola_total", 0)) if filas else 0
        return total, filas
    except Exception:
        filas = list(qs[:5])
        total = qs.count() if len(filas) == 5 else len(filas)
        return total, filas


def top5(qs, user):
    if solo_conteo(user):
        return []
    return list(qs[:5])


def dinero(monto):
    try:
        valor = float(monto or 0)
    except (TypeError, ValueError):
        valor = 0
    return f"${valor:,.0f}"
