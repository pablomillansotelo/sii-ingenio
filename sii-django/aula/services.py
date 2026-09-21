from decimal import Decimal

from aula.models import CalificacionActividad, Kardex


def actualizar_kardex(inscripcion):
    """Promedio ponderado por valor de actividad → inscripción y kardex."""
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
