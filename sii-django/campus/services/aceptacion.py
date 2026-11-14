from django.utils import timezone

from sii.models import AceptacionCarga, Inscripcion


def ventana_abierta(periodo, hoy=None):
    if periodo is None:
        return False
    if not periodo.ventana_aceptacion_inicio or not periodo.ventana_aceptacion_fin:
        return False
    hoy = hoy or timezone.localdate()
    return periodo.ventana_aceptacion_inicio <= hoy <= periodo.ventana_aceptacion_fin


def carga_del_periodo(alumno, periodo):
    if alumno is None or periodo is None:
        return Inscripcion.objects.none()
    return (
        Inscripcion.objects.filter(alumno=alumno, periodo=periodo, estado="activo")
        .select_related("curso", "id_edicion", "aceptacion")
        .order_by("curso__nombre")
    )
