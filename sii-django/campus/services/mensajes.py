from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.exceptions import ValidationError

from campus.models import Hilo, HiloParticipante, MensajeCampus, MensajeLectura
from sii.identity import alumno_para_usuario, docente_para_usuario, es_administrador
from sii.models import DocenteCurso, Inscripcion
from sii.services.expediente import validar_archivo as validar_adjunto


def hilos_visibles(user):
    if es_administrador(user):
        return Hilo.objects.filter(Q(para_control=True) | Q(participantes__user_id=user.pk)).distinct()
    return Hilo.objects.filter(participantes__user_id=user.pk).distinct()


def puede_ver(user, hilo):
    if hilo.para_control and es_administrador(user):
        return True
    return HiloParticipante.objects.filter(hilo=hilo, user_id=user.pk).exists()


def resumen_hilos(user):
    leidos_ids = set(
        MensajeLectura.objects.filter(user_id=user.pk).values_list("mensaje_id", flat=True)
    )
    filas = []
    for hilo in hilos_visibles(user):
        ultimo = hilo.mensajes.exclude(autor_id=user.pk).last()
        leido = ultimo is None or ultimo.pk in leidos_ids
        filas.append({"hilo": hilo, "leido": leido})
    return filas


def no_leidos(user):
    hilos = hilos_visibles(user)
    mensajes = MensajeCampus.objects.filter(hilo__in=hilos).exclude(autor_id=user.pk)
    leidos = MensajeLectura.objects.filter(user_id=user.pk).values_list("mensaje_id", flat=True)
    return mensajes.exclude(pk__in=leidos).count()


def marcar_hilo_leido(user, hilo):
    ids = hilo.mensajes.exclude(autor_id=user.pk).values_list("pk", flat=True)
    existentes = set(
        MensajeLectura.objects.filter(user_id=user.pk, mensaje_id__in=ids).values_list("mensaje_id", flat=True)
    )
    MensajeLectura.objects.bulk_create(
        [MensajeLectura(mensaje_id=mid, user_id=user.pk) for mid in ids if mid not in existentes]
    )


def destinos_alumno(alumno):
    destinos = [{"clave": "control", "label": "Control escolar"}]
    if alumno is None:
        return destinos
    cursos = Inscripcion.objects.filter(alumno=alumno, estado="activo").values_list("curso_id", flat=True)
    asignaciones = DocenteCurso.objects.filter(curso_id__in=cursos).select_related("docente")
    vistos = set()
    for asig in asignaciones:
        uid = asig.docente.user_id
        if not uid or uid in vistos:
            continue
        vistos.add(uid)
        destinos.append(
            {
                "clave": f"docente:{uid}",
                "label": f"Docente {asig.docente.nombre} {asig.docente.apellido}",
            }
        )
    return destinos


def abrir_hilo(user, asunto, cuerpo, destino, archivo=None):
    asunto = (asunto or "").strip()
    cuerpo = (cuerpo or "").strip()
    if not asunto or not cuerpo:
        raise ValidationError("Asunto y mensaje son obligatorios.")
    if archivo:
        validar_adjunto(archivo)
    hilo = Hilo(asunto=asunto, creado_por_id=user.pk, para_control=destino == "control")
    if destino == "control":
        if not (alumno_para_usuario(user) or es_administrador(user)):
            raise ValidationError("No puedes escribir a control escolar.")
        hilo.save()
        HiloParticipante.objects.get_or_create(hilo=hilo, user_id=user.pk)
    elif str(destino).startswith("docente:"):
        docente_uid = int(str(destino).split(":", 1)[1])
        alumno = alumno_para_usuario(user)
        if alumno is None:
            raise ValidationError("Solo el alumno escribe a su docente desde aquí.")
        permitidos = {d["clave"] for d in destinos_alumno(alumno)}
        if destino not in permitidos:
            raise ValidationError("Ese docente no es de tus grupos.")
        hilo.save()
        HiloParticipante.objects.get_or_create(hilo=hilo, user_id=user.pk)
        HiloParticipante.objects.get_or_create(hilo=hilo, user_id=docente_uid)
    elif str(destino).startswith("alumno:"):
        if not (es_administrador(user) or docente_para_usuario(user)):
            raise ValidationError("Solo staff o docente inician un mensaje hacia un alumno.")
        alumno_uid = int(str(destino).split(":", 1)[1])
        hilo.para_control = es_administrador(user)
        hilo.save()
        HiloParticipante.objects.get_or_create(hilo=hilo, user_id=user.pk)
        HiloParticipante.objects.get_or_create(hilo=hilo, user_id=alumno_uid)
    else:
        raise ValidationError("Elige un destinatario.")
    MensajeCampus.objects.create(hilo=hilo, autor_id=user.pk, cuerpo=cuerpo, archivo=archivo)
    return hilo


def responder(user, hilo, cuerpo, archivo=None):
    if not puede_ver(user, hilo):
        raise ValidationError("No puedes responder este hilo.")
    cuerpo = (cuerpo or "").strip()
    if not cuerpo and not archivo:
        raise ValidationError("Escribe un mensaje.")
    if archivo:
        validar_adjunto(archivo)
    if es_administrador(user):
        HiloParticipante.objects.get_or_create(hilo=hilo, user_id=user.pk)
    return MensajeCampus.objects.create(hilo=hilo, autor_id=user.pk, cuerpo=cuerpo or "(adjunto)", archivo=archivo)


def alumnos_contacto(user):
    User = get_user_model()
    from sii.models import Alumno

    if es_administrador(user):
        return Alumno.objects.exclude(user_id=None).order_by("apellido", "nombre")
    docente = docente_para_usuario(user)
    if docente is None:
        return Alumno.objects.none()
    curso_ids = DocenteCurso.objects.filter(docente=docente).values_list("curso_id", flat=True)
    user_ids = (
        Inscripcion.objects.filter(curso_id__in=curso_ids, estado="activo")
        .exclude(alumno__user_id=None)
        .values_list("alumno__user_id", flat=True)
    )
    return Alumno.objects.filter(user_id__in=user_ids).order_by("apellido", "nombre")
