from django.db.models import Q
from django.utils import timezone

from aula.models import AvisoGrupo
from campus.models import AvisoInstitucional, AvisoLectura
from sii.models import Inscripcion


def avisos_vigentes_qs(alumno, hoy=None):
    hoy = hoy or timezone.localdate()
    qs = AvisoInstitucional.objects.filter(publicado=True)
    qs = qs.filter(Q(vigencia_inicio__isnull=True) | Q(vigencia_inicio__lte=hoy))
    qs = qs.filter(Q(vigencia_fin__isnull=True) | Q(vigencia_fin__gte=hoy))
    if alumno is None:
        return qs.none()
    periodos = Inscripcion.objects.filter(alumno=alumno).exclude(estado="cancelado").values_list(
        "periodo_id", flat=True
    )
    return qs.filter(Q(periodo__isnull=True) | Q(periodo_id__in=periodos))


def ids_leidos(alumno):
    if alumno is None:
        return set()
    return set(AvisoLectura.objects.filter(alumno=alumno).values_list("aviso_id", flat=True))


def bandeja_avisos(alumno, filtro=None, hoy=None):
    hoy = hoy or timezone.localdate()
    leidos = ids_leidos(alumno)
    items = []
    for aviso in avisos_vigentes_qs(alumno, hoy):
        leido = aviso.pk in leidos
        if filtro == "leidos" and not leido:
            continue
        if filtro == "no_leidos" and leido:
            continue
        items.append({"aviso": aviso, "leido": leido, "fuente": "institucional"})
    # Avisos de grupo: lectura agregada, no se migran ni se marcan aquí.
    if alumno is not None and filtro != "leidos":
        inscripciones = list(
            Inscripcion.objects.filter(alumno=alumno, estado="activo").values_list("id_edicion_id", "curso_id")
        )
        if inscripciones:
            edicion_ids = [e[0] for e in inscripciones if e[0]]
            curso_ids = [e[1] for e in inscripciones]
            filtro_grupo = Q(edicion_id__isnull=True, curso_id__in=curso_ids)
            if edicion_ids:
                filtro_grupo |= Q(edicion_id__in=edicion_ids)
            grupos = AvisoGrupo.objects.filter(publicado=True).filter(filtro_grupo)
            for aviso in grupos:
                items.append({"aviso": aviso, "leido": False, "fuente": "grupo"})
    importantes_pendientes = [
        item["aviso"]
        for item in items
        if item["fuente"] == "institucional"
        and not item["leido"]
        and item["aviso"].tipo == AvisoInstitucional.TIPO_IMPORTANTE
    ]
    return {"items": items, "importantes_pendientes": importantes_pendientes}


def marcar_leido(alumno, aviso):
    if alumno is None:
        return None
    lectura, _ = AvisoLectura.objects.get_or_create(alumno=alumno, aviso=aviso)
    return lectura
