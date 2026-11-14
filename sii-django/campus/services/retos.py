from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from aula.models import CalificacionActividad
from campus.models import RetoSemanal
from campus.services.ludico import acreditar
from sii.models import Inscripcion

TZ = ZoneInfo("America/Mexico_City")
XP_RETO_SEMANA = 20
META_ENTREGAS = 1


def lunes_semana(ahora=None):
    ahora = ahora or timezone.now()
    if timezone.is_naive(ahora):
        ahora = timezone.make_aware(ahora, timezone.get_current_timezone())
    local = ahora.astimezone(TZ)
    dia = local.date()
    return dia - timedelta(days=dia.weekday())


def _entregas_en_semana(inscripcion, lunes):
    domingo = lunes + timedelta(days=6)
    return CalificacionActividad.objects.filter(
        inscripcion=inscripcion,
        entregado=True,
        fecha_entrega__gte=lunes,
        fecha_entrega__lte=domingo,
    ).count()


def sincronizar_retos(alumno, ahora=None):
    if alumno is None:
        return []
    lunes = lunes_semana(ahora)
    retos = []
    for ins in Inscripcion.objects.filter(alumno=alumno, estado="activo").select_related("curso"):
        reto, _ = RetoSemanal.objects.get_or_create(
            inscripcion=ins,
            semana=lunes,
            defaults={"alumno": alumno, "meta": META_ENTREGAS},
        )
        progreso = min(reto.meta, _entregas_en_semana(ins, lunes))
        campos = []
        if reto.progreso != progreso:
            reto.progreso = progreso
            campos.append("progreso")
        if progreso >= reto.meta and reto.completado_en is None:
            reto.completado_en = timezone.now()
            campos.append("completado_en")
            acreditar(
                alumno,
                XP_RETO_SEMANA,
                f"Reto semanal: {ins.curso.nombre}",
                f"reto-sem-{ins.pk}-{lunes.isoformat()}",
            )
        if campos:
            reto.save(update_fields=campos)
        retos.append(reto)
    return retos
