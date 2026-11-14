from django.db.models import Q
from django.utils import timezone

from campus.models import Noticia


def noticias_publicadas_qs(hoy=None):
    hoy = hoy or timezone.localdate()
    qs = Noticia.objects.filter(publicada=True)
    qs = qs.filter(Q(vigencia_inicio__isnull=True) | Q(vigencia_inicio__lte=hoy))
    qs = qs.filter(Q(vigencia_fin__isnull=True) | Q(vigencia_fin__gte=hoy))
    return qs.order_by("-creada_en")


def noticias_publicadas(hoy=None, limite=5):
    return noticias_publicadas_qs(hoy)[:limite]
