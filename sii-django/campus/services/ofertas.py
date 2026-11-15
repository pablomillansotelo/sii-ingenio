from decimal import Decimal

from django.db.models import F, Q

from sii.models import Inscripcion
from ventas.models import EdicionCurso, SolicitudOferta


def qs_ediciones_vigentes():
    return (
        EdicionCurso.objects.select_related("id_curso")
        .filter(
            activo=True,
            estado__in=EdicionCurso.ESTADOS_ABIERTOS,
            id_curso__activo=True,
            cupo_ocupado__lt=F("cupo_maximo"),
        )
    )


def qs_recomendadas():
    return qs_ediciones_vigentes().filter(Q(id_curso__destacado=True) | Q(educacion_continua=True)).order_by(
        "-id_curso__destacado", "fecha_inicio", "codigo_edicion"
    )


def qs_educacion_continua():
    return qs_ediciones_vigentes().filter(educacion_continua=True).order_by("fecha_inicio", "codigo_edicion")


def _tarjeta(edicion, alumno):
    precio = edicion.precio_aplicable
    sin_costo = precio is None or Decimal(precio) == 0
    ya_inscrito = False
    ya_solicitado = False
    if alumno:
        ya_inscrito = Inscripcion.objects.filter(alumno=alumno, id_edicion=edicion).exists()
        ya_solicitado = SolicitudOferta.objects.filter(alumno=alumno, edicion=edicion).exists()
    if edicion.id_curso.destacado:
        etiqueta = "Destacado"
    elif edicion.educacion_continua:
        etiqueta = "Educación continua"
    else:
        etiqueta = "Recomendado"
    return {
        "edicion": edicion,
        "curso": edicion.id_curso,
        "precio": precio,
        "sin_costo": sin_costo,
        "cupo_disponible": edicion.cupo_disponible,
        "etiqueta": etiqueta,
        "ya_inscrito": ya_inscrito,
        "ya_solicitado": ya_solicitado,
    }


def tarjetas_recomendadas(alumno=None):
    return [_tarjeta(edicion, alumno) for edicion in qs_recomendadas()]


def tarjetas_educacion_continua(alumno=None):
    return [_tarjeta(edicion, alumno) for edicion in qs_educacion_continua()]


def solicitar_inscripcion(alumno, edicion):
    """Crea solicitud comercial. No reserva cupo ni crea Inscripcion."""
    vigente = qs_ediciones_vigentes().filter(pk=edicion.pk).exists()
    if not vigente:
        raise ValueError("Esta edición no está abierta o no tiene cupo.")
    if Inscripcion.objects.filter(alumno=alumno, id_edicion=edicion).exists():
        raise ValueError("Ya estás inscrito en esta edición.")
    solicitud, created = SolicitudOferta.objects.get_or_create(alumno=alumno, edicion=edicion)
    return solicitud, created
