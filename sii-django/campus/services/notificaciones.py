from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from aula.models import Actividad, CalificacionActividad
from campus.models import AvisoInstitucional, Notificacion
from campus.services.avisos import avisos_vigentes_qs
from campus.services.cuenta import estado_cuenta
from sii.models import Inscripcion


def emitir(user_id, tipo, clave, titulo, cuerpo="", url=""):
    if not user_id:
        return None
    try:
        obj, _ = Notificacion.objects.get_or_create(
            user_id=user_id,
            tipo=tipo,
            clave=str(clave)[:80],
            defaults={"titulo": titulo, "cuerpo": cuerpo[:280], "url": url[:200]},
        )
        return obj
    except Exception:
        return None


def sincronizar(user, alumno):
    if user is None or not getattr(user, "pk", None):
        return
    try:
        _sincronizar(user, alumno)
    except Exception:
        return


def _sincronizar(user, alumno):
    if alumno is None:
        return
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=7)
    inscripciones = list(
        Inscripcion.objects.filter(alumno=alumno, estado="activo").select_related("curso")
    )
    curso_ids = [i.curso_id for i in inscripciones]
    edicion_ids = [i.id_edicion_id for i in inscripciones if i.id_edicion_id]
    if curso_ids:
        acts = Actividad.objects.filter(curso_id__in=curso_ids, estado="activa")
        if edicion_ids:
            from django.db.models import Q

            acts = acts.filter(Q(edicion_id__in=edicion_ids) | Q(edicion_id__isnull=True))
        for act in acts:
            url = reverse("aula_curso", args=[act.curso_id])
            if act.edicion_id:
                url = reverse("aula_grupo", args=[act.curso_id, act.edicion_id])
            emitir(
                user.pk,
                Notificacion.TIPO_ACTIVIDAD,
                f"act-{act.pk}",
                f"Actividad: {act.nombre}",
                act.curso.nombre,
                url,
            )
            if act.fecha_limite and hoy <= act.fecha_limite <= limite:
                emitir(
                    user.pk,
                    Notificacion.TIPO_ACTIVIDAD,
                    f"vence-{act.pk}",
                    f"Por vencer: {act.nombre}",
                    f"Límite {act.fecha_limite}",
                    url,
                )
        regs = CalificacionActividad.objects.filter(
            inscripcion__in=inscripciones, calificacion__isnull=False
        ).select_related("actividad")
        for reg in regs:
            emitir(
                user.pk,
                Notificacion.TIPO_CALIFICACION,
                f"cal-{reg.pk}",
                f"Calificación en {reg.actividad.nombre}",
                str(reg.calificacion),
                reverse("campus_kardex"),
            )
    for aviso in avisos_vigentes_qs(alumno).filter(tipo=AvisoInstitucional.TIPO_IMPORTANTE):
        emitir(
            user.pk,
            Notificacion.TIPO_AVISO,
            f"aviso-{aviso.pk}",
            aviso.titulo,
            (aviso.cuerpo or "")[:280],
            reverse("campus_avisos"),
        )
    cuenta = estado_cuenta(user)
    if cuenta["hay_deuda"]:
        emitir(
            user.pk,
            Notificacion.TIPO_DEUDA,
            "deuda-actual",
            "Tienes un saldo pendiente",
            f"Saldo ${cuenta['saldo']}",
            reverse("campus_estado_cuenta"),
        )


def lista(user):
    return Notificacion.objects.filter(user_id=user.pk)


def no_leidas(user):
    return lista(user).filter(leida_en__isnull=True).count()


def marcar_una(user, pk):
    Notificacion.objects.filter(user_id=user.pk, pk=pk, leida_en__isnull=True).update(
        leida_en=timezone.now()
    )


def marcar_todas(user):
    lista(user).filter(leida_en__isnull=True).update(leida_en=timezone.now())
