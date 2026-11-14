"""Hitos del periodo del alumno. HorarioSlot es otro concepto (semana)."""
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from aula.models import Actividad
from campus.services.cursos import periodo_vigente
from sii.models import Inscripcion, Periodo


def periodo_del_alumno(alumno, hoy=None):
    hoy = hoy or timezone.localdate()
    if alumno is None:
        return None
    vigente = periodo_vigente(hoy)
    if vigente and Inscripcion.objects.filter(alumno=alumno, periodo=vigente).exclude(estado="cancelado").exists():
        return vigente
    ins = (
        Inscripcion.objects.filter(alumno=alumno)
        .exclude(estado="cancelado")
        .select_related("periodo")
        .order_by("-periodo__fecha_inicio")
        .first()
    )
    return ins.periodo if ins else None


def proximo_periodo(periodo):
    if periodo is None:
        return None
    return (
        Periodo.objects.filter(fecha_inicio__gt=periodo.fecha_fin)
        .order_by("fecha_inicio")
        .first()
    )


def hitos_calendario(alumno, hoy=None):
    hoy = hoy or timezone.localdate()
    periodo = periodo_del_alumno(alumno, hoy)
    if alumno is None or periodo is None:
        return {"periodo": None, "proximo": None, "hitos": []}

    hitos = [
        {
            "fecha": periodo.fecha_inicio,
            "titulo": "Inicio del periodo",
            "tipo": "periodo",
            "estado": "pasado" if periodo.fecha_inicio < hoy else "proximo",
            "url": None,
        },
        {
            "fecha": periodo.fecha_fin,
            "titulo": "Fin del periodo",
            "tipo": "periodo",
            "estado": "pasado" if periodo.fecha_fin < hoy else "proximo",
            "url": None,
        },
    ]
    calif = periodo.fecha_publicacion_calificaciones or periodo.fecha_fin
    hitos.append(
        {
            "fecha": calif,
            "titulo": "Publicación de calificaciones",
            "tipo": "calificaciones",
            "estado": "pasado" if calif < hoy else "proximo",
            "url": reverse("sii_kardex"),
        }
    )

    inscripciones = list(
        Inscripcion.objects.filter(alumno=alumno, periodo=periodo, estado="activo").select_related("curso")
    )
    edicion_ids = [i.id_edicion_id for i in inscripciones if i.id_edicion_id]
    curso_ids = [i.curso_id for i in inscripciones]
    acts = Actividad.objects.filter(curso_id__in=curso_ids)
    if edicion_ids:
        acts = acts.filter(Q(edicion_id__in=edicion_ids) | Q(edicion_id__isnull=True, curso_id__in=curso_ids))
    else:
        acts = acts.filter(edicion_id__isnull=True)
    for act in acts.order_by("fecha_limite", "nombre"):
        vencida = act.fecha_limite < hoy
        hitos.append(
            {
                "fecha": act.fecha_limite,
                "titulo": f"Entrega: {act.nombre}",
                "tipo": "entrega",
                "estado": "vencida" if vencida else "proximo",
                "url": reverse("aula_entregar", args=[act.pk]),
                "curso": act.curso.nombre,
            }
        )

    proximo = proximo_periodo(periodo)
    if proximo:
        hitos.append(
            {
                "fecha": proximo.fecha_inicio,
                "titulo": f"Próximo periodo: {proximo.nombre}",
                "tipo": "proximo_periodo",
                "estado": "proximo",
                "url": None,
            }
        )
    hitos.sort(key=lambda h: (h["fecha"], h["titulo"]))
    return {"periodo": periodo, "proximo": proximo, "hitos": hitos}
