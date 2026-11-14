"""Avance académico oficial del alumno (kardex SII, no gamificación).

Sin un plan de estudios modelado, Y es el número de *cursos distintos*
en los que el alumno se ha inscrito históricamente (incluye bajas).
No es un total mágico hardcoded.

X (cursadas acreditadas) son cursos distintos con calificación oficial
>= CALIFICACION_MINIMA y estado distinto de cancelado.

El promedio solo promedia renglones con nota oficial (Inscripcion.calificacion
o renglón de acta publicada/cerrada). Materias en curso (sin nota) no
entran como cero. Las bajas no cuentan como acreditadas.
"""
from decimal import Decimal, ROUND_HALF_UP

from sii.models import CALIFICACION_MINIMA, Inscripcion

ACTA_OFICIAL = ("publicada", "cerrada")


def calificacion_oficial(inscripcion):
    renglon = getattr(inscripcion, "renglon_acta", None)
    if renglon is not None:
        acta = getattr(renglon, "acta", None)
        if acta is not None and acta.estado in ACTA_OFICIAL and renglon.calificacion is not None:
            return renglon.calificacion
    return inscripcion.calificacion


def es_acreditada(inscripcion):
    if inscripcion.estado == "cancelado":
        return False
    nota = calificacion_oficial(inscripcion)
    if nota is None:
        return False
    return nota >= CALIFICACION_MINIMA


def avance_academico(alumno):
    vacio = {
        "tiene_inscripciones": False,
        "promedio": None,
        "porcentaje": None,
        "materias_x": 0,
        "materias_y": 0,
        "plan_etiqueta": "Sin plan de estudios formal: Y son las materias distintas inscritas en tu historial.",
    }
    if alumno is None:
        return vacio
    inscripciones = list(
        Inscripcion.objects.filter(alumno=alumno)
        .select_related("curso", "periodo", "renglon_acta__acta")
        .order_by("-periodo__fecha_inicio", "-id")
    )
    if not inscripciones:
        return vacio

    cursos_y = {ins.curso_id for ins in inscripciones}
    cursos_x = {ins.curso_id for ins in inscripciones if es_acreditada(ins)}
    notas = [calificacion_oficial(ins) for ins in inscripciones if ins.estado != "cancelado"]
    notas = [n for n in notas if n is not None]
    promedio = None
    if notas:
        promedio = (sum(notas, Decimal("0")) / Decimal(len(notas))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    y = len(cursos_y)
    x = len(cursos_x)
    porcentaje = None
    if y:
        porcentaje = int((Decimal(x) / Decimal(y) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return {
        "tiene_inscripciones": True,
        "promedio": promedio,
        "porcentaje": porcentaje,
        "materias_x": x,
        "materias_y": y,
        "plan_etiqueta": "Sin plan de estudios formal: Y son las materias distintas inscritas en tu historial.",
    }
