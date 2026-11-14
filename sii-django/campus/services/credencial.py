from django.core.signing import BadSignature, dumps, loads
from django.utils import timezone

from sii.models import Inscripcion


def inscripcion_vigente(alumno):
    if alumno is None:
        return None
    hoy = timezone.localdate()
    return (
        Inscripcion.objects.filter(alumno=alumno, estado="activo")
        .filter(periodo__fecha_inicio__lte=hoy, periodo__fecha_fin__gte=hoy)
        .select_related("periodo")
        .order_by("-periodo__fecha_inicio")
        .first()
    )


def es_valida(alumno):
    if alumno is None:
        return False
    if alumno.estado != "activo":
        return False
    return inscripcion_vigente(alumno) is not None


def token_de(alumno):
    return dumps({"a": alumno.pk}, salt="campus.credencial")


def alumno_de_token(token):
    from sii.models import Alumno

    try:
        data = loads(token, salt="campus.credencial")
    except BadSignature:
        return None
    return Alumno.objects.filter(pk=data.get("a")).first()


def ficha_credencial(alumno):
    ins = inscripcion_vigente(alumno)
    valida = es_valida(alumno)
    return {
        "alumno": alumno,
        "valida": valida,
        "periodo": ins.periodo if ins else None,
        "token": token_de(alumno) if alumno else "",
        "estado_etiqueta": "Vigente" if valida else "No válida",
        "motivo": _motivo(alumno, ins),
    }


def _motivo(alumno, ins):
    if alumno is None:
        return "No hay expediente."
    if alumno.estado != "activo":
        return f"El expediente está {alumno.estado}; esta credencial no es válida."
    if ins is None:
        return "No hay inscripción activa en el periodo vigente."
    return ""
