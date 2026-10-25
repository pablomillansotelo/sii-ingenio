from decimal import Decimal

from django.db.models import Q
from django.urls import reverse

from aula.models import Actividad, CalificacionActividad, Kardex
from sii.models import Inscripcion


def actualizar_kardex(inscripcion):
    """Promedio ponderado por valor de actividad → inscripción y kardex."""
    from sii.actas import acta_congela_inscripcion

    if acta_congela_inscripcion(inscripcion):
        return inscripcion.calificacion

    filas = CalificacionActividad.objects.filter(
        inscripcion=inscripcion,
        calificacion__isnull=False,
    ).select_related("actividad")
    peso_total = sum((fila.actividad.valor or Decimal("0")) for fila in filas)
    if peso_total <= 0:
        promedio = None
    else:
        puntos = sum((fila.calificacion or Decimal("0")) for fila in filas)
        promedio = (Decimal("100") * puntos / peso_total).quantize(Decimal("0.01"))

    inscripcion.calificacion = promedio
    inscripcion.save(update_fields=["calificacion"])
    kardex, _ = Kardex.objects.get_or_create(inscripcion=inscripcion)
    kardex.calificacion_final = promedio
    kardex.save(update_fields=["calificacion_final", "fecha_actualizacion"])
    return promedio


def curso_sii_de_edicion(edicion):
    if edicion is None:
        return None
    producto = getattr(edicion, "id_curso", None)
    if producto is None:
        return None
    return getattr(producto, "id_curso", None)


def url_aula_grupo(curso, edicion=None):
    if edicion is not None:
        return reverse("aula_grupo", args=[curso.pk, edicion.pk])
    return reverse("aula_curso", args=[curso.pk])


def actividades_del_grupo(curso, edicion=None):
    qs = Actividad.objects.filter(curso=curso)
    if edicion is not None:
        qs = qs.filter(Q(edicion=edicion) | Q(edicion__isnull=True))
    return qs.select_related("seccion", "edicion")


def roster_del_grupo(curso, edicion=None):
    qs = Inscripcion.objects.filter(curso=curso, estado="activo").select_related(
        "alumno", "periodo", "id_edicion"
    )
    if edicion is not None:
        qs = qs.filter(id_edicion=edicion)
    return qs.order_by("alumno__apellido", "alumno__nombre")


def inscripcion_en_grupo(alumno, curso, edicion=None):
    if alumno is None:
        return None
    qs = Inscripcion.objects.filter(alumno=alumno, curso=curso).select_related(
        "periodo", "id_edicion"
    )
    if edicion is not None:
        return qs.filter(id_edicion=edicion).order_by("-periodo__fecha_inicio", "-id").first()
    return qs.order_by("-periodo__fecha_inicio", "-id").first()


def alumno_pertenece_al_grupo(inscripcion, curso, edicion=None):
    if inscripcion is None or inscripcion.curso_id != curso.pk:
        return False
    if edicion is None:
        return True
    if inscripcion.id_edicion_id is None:
        return True
    return inscripcion.id_edicion_id == edicion.pk


def entregas_pendientes_qs(user):
    from sii.identity import docente_para_usuario, ediciones_visibles, es_administrador

    qs = CalificacionActividad.objects.filter(
        entregado=True, calificacion__isnull=True
    ).select_related("actividad__curso", "actividad__edicion", "inscripcion__alumno")
    if es_administrador(user):
        return qs
    docente = docente_para_usuario(user)
    if docente is None:
        return qs.none()
    edicion_ids = list(ediciones_visibles(user).values_list("pk", flat=True))
    curso_ids = docente.cursos_asignados.values_list("curso_id", flat=True)
    alcance = Q(actividad__curso_id__in=curso_ids)
    if edicion_ids:
        alcance &= Q(actividad__edicion_id__in=edicion_ids) | Q(actividad__edicion__isnull=True)
    return qs.filter(alcance)
