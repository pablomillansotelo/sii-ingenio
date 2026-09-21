"""Actas de calificación final y congelado de periodo."""
from django.db import transaction
from django.utils import timezone

from sii.models import ActaFinal, ActaRenglon, Inscripcion, Periodo


def acta_de(curso, periodo):
    acta, _ = ActaFinal.objects.get_or_create(curso=curso, periodo=periodo)
    return acta


def sincronizar_renglones(acta):
    inscripciones = Inscripcion.objects.filter(
        curso=acta.curso, periodo=acta.periodo, estado="activo"
    ).select_related("alumno")
    existentes = {r.inscripcion_id: r for r in acta.renglones.select_related("inscripcion")}
    for inscripcion in inscripciones:
        renglon = existentes.get(inscripcion.pk)
        if renglon is None:
            renglon = ActaRenglon(acta=acta, inscripcion=inscripcion)
        if renglon.calificacion is None and inscripcion.calificacion is not None:
            renglon.calificacion = inscripcion.calificacion
        renglon.aplicar_minima()
        renglon.save()
    return list(acta.renglones.select_related("inscripcion__alumno").order_by("inscripcion__alumno__apellido"))


def publicar_acta(acta, user, calificaciones=None):
    if acta.periodo.cerrado or acta.estado == ActaFinal.ESTADO_CERRADA:
        raise ValueError("El periodo ya está cerrado. El acta no se edita.")
    with transaction.atomic():
        renglones = sincronizar_renglones(acta)
        if calificaciones:
            por_id = {r.pk: r for r in renglones}
            for renglon_id, nota in calificaciones.items():
                renglon = por_id.get(int(renglon_id))
                if renglon is None:
                    continue
                renglon.calificacion = nota
                renglon.aplicar_minima()
                renglon.save(update_fields=["calificacion", "acreditado"])
        for renglon in acta.renglones.select_related("inscripcion"):
            if renglon.calificacion is None:
                continue
            inscripcion = renglon.inscripcion
            inscripcion.calificacion = renglon.calificacion
            inscripcion.save(update_fields=["calificacion"])
        acta.estado = ActaFinal.ESTADO_PUBLICADA
        acta.publicada_por_id = getattr(user, "pk", None)
        acta.publicada_en = timezone.now()
        acta.save(update_fields=["estado", "publicada_por_id", "publicada_en"])
    return acta


def cerrar_periodo(periodo, user=None):
    if periodo.cerrado:
        return periodo
    with transaction.atomic():
        cursos_ids = list(
            Inscripcion.objects.filter(periodo=periodo)
            .values_list("curso_id", flat=True)
            .distinct()
        )
        from sii.models import Curso

        for curso_id in cursos_ids:
            curso = Curso.objects.get(pk=curso_id)
            acta = acta_de(curso, periodo)
            if acta.estado == ActaFinal.ESTADO_BORRADOR:
                publicar_acta(acta, user)
            acta.estado = ActaFinal.ESTADO_CERRADA
            acta.save(update_fields=["estado"])
        periodo.cerrado = True
        periodo.save(update_fields=["cerrado"])
    return periodo


def acta_congela_inscripcion(inscripcion):
    if inscripcion.periodo_id and Periodo.objects.filter(pk=inscripcion.periodo_id, cerrado=True).exists():
        return True
    return ActaFinal.objects.filter(
        curso_id=inscripcion.curso_id,
        periodo_id=inscripcion.periodo_id,
        estado__in=(ActaFinal.ESTADO_PUBLICADA, ActaFinal.ESTADO_CERRADA),
    ).exists()


def grupos_de_acta(user):
    """Pares curso+periodo visibles para actas."""
    from sii.identity import cursos_visibles, es_administrador, docente_para_usuario

    cursos = cursos_visibles(user)
    if not es_administrador(user):
        docente = docente_para_usuario(user)
        if docente is None:
            cursos = cursos.none()
        else:
            cursos = cursos.filter(pk__in=docente.cursos_asignados.values_list("curso_id", flat=True))
    pares = (
        Inscripcion.objects.filter(curso__in=cursos)
        .values("curso_id", "periodo_id")
        .distinct()
    )
    return pares
