"""Candado de retos por sección: lúdico por defecto (no tapa material publicado)."""

from aula.models import Actividad, CalificacionActividad
from campus.services.ludico import acreditar

XP_SECCION = 15


def entregas_de(inscripcion):
    if inscripcion is None:
        return {}
    return {
        fila.actividad_id: fila
        for fila in CalificacionActividad.objects.filter(inscripcion=inscripcion)
    }


def seccion_completa(seccion, entregas):
    acts = list(Actividad.objects.filter(seccion=seccion))
    if not acts:
        return True
    return all(entregas.get(act.pk) and entregas[act.pk].entregado for act in acts)


def seccion_bloqueada_para(actividad, inscripcion):
    if actividad.seccion_id is None or inscripcion is None:
        return False
    entregas = entregas_de(inscripcion)
    previas = list(
        actividad.seccion.__class__.objects.filter(
            curso=actividad.seccion.curso,
            edicion_id=actividad.seccion.edicion_id,
            orden__lt=actividad.seccion.orden,
        ).order_by("orden", "id")
    )
    for previa in previas:
        if not seccion_completa(previa, entregas):
            return True
    return False


def anotar_bloques(bloques, inscripcion, edicion, alumno=None):
    entregas = entregas_de(inscripcion)
    duro = bool(edicion and getattr(edicion, "candado_academico", False))
    previa_completa = True
    for bloque in bloques:
        bloque["reto_bloqueado"] = not previa_completa
        bloque["candado_duro"] = duro and bloque["reto_bloqueado"]
        completa = seccion_completa(bloque["seccion"], entregas)
        if completa and inscripcion and alumno and not bloque["reto_bloqueado"]:
            acreditar(
                alumno,
                XP_SECCION,
                f"Sección: {bloque['seccion'].titulo}",
                f"seccion-{bloque['seccion'].pk}",
            )
        previa_completa = completa
    return bloques
