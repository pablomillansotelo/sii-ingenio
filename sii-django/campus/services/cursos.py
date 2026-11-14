"""Tarjetas del curso actual.

Progreso = actividades entregadas o calificadas / actividades del curso
(y de la edición, si la inscripción tiene grupo). Si no hay actividades,
el denominador son las secciones publicadas con material; el numerador
queda en 0 porque aún no hay rastro de «visto» por alumno.
No usa XP ni aula.Kardex.
"""
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from aula.models import Actividad, CalificacionActividad, SeccionTema
from sii.models import Inscripcion, Periodo


def periodo_vigente(hoy=None):
    hoy = hoy or timezone.localdate()
    return (
        Periodo.objects.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy)
        .order_by("-fecha_inicio")
        .first()
    )


def _actividades_de(inscripcion):
    qs = Actividad.objects.filter(curso=inscripcion.curso)
    if inscripcion.id_edicion_id:
        qs = qs.filter(Q(edicion_id=inscripcion.id_edicion_id) | Q(edicion_id__isnull=True))
    return qs


def progreso_inscripcion(inscripcion):
    actividades = _actividades_de(inscripcion)
    total = actividades.count()
    if total:
        hechos = (
            CalificacionActividad.objects.filter(inscripcion=inscripcion, actividad__in=actividades)
            .filter(Q(entregado=True) | Q(calificacion__isnull=False))
            .values("actividad_id")
            .distinct()
            .count()
        )
        pct = int(round(100 * hechos / total)) if total else 0
        return {"hechos": hechos, "total": total, "porcentaje": pct, "unidad": "actividades"}
    secciones = SeccionTema.objects.filter(curso=inscripcion.curso)
    if inscripcion.id_edicion_id:
        secciones = secciones.filter(Q(edicion_id=inscripcion.id_edicion_id) | Q(edicion_id__isnull=True))
    total_s = secciones.count()
    return {"hechos": 0, "total": total_s, "porcentaje": 0, "unidad": "secciones"}


def url_aula(inscripcion):
    if inscripcion.id_edicion_id:
        return reverse("aula_grupo", args=[inscripcion.curso_id, inscripcion.id_edicion_id])
    return reverse("aula_curso", args=[inscripcion.curso_id])


def tarjetas_curso_actual(alumno, hoy=None):
    hoy = hoy or timezone.localdate()
    periodo = periodo_vigente(hoy)
    if alumno is None or periodo is None:
        return {"periodo": periodo, "tarjetas": []}
    qs = (
        Inscripcion.objects.filter(alumno=alumno, periodo=periodo, estado="activo")
        .select_related("curso", "periodo", "id_edicion")
        .order_by("curso__nombre")
    )
    tarjetas = []
    for inscripcion in qs:
        puede = bool(inscripcion.puede_cursar)
        tarjetas.append(
            {
                "inscripcion": inscripcion,
                "curso": inscripcion.curso,
                "periodo": inscripcion.periodo,
                "edicion": inscripcion.id_edicion,
                "progreso": progreso_inscripcion(inscripcion),
                "puede_cursar": puede,
                "url_aula": url_aula(inscripcion) if puede else None,
            }
        )
    return {"periodo": periodo, "tarjetas": tarjetas}
