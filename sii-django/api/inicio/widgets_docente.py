from datetime import timedelta

from django.db.models import Count, Exists, IntegerField, Min, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse

from api.inicio.cache import memo, memo_user, solo_conteo
from api.inicio.registro import registrar
from api.inicio.utils import cola, reverse_home, top5, with_from_home
from api.inicio.widgets import Item, Widget, WidgetData
from aula.models import Actividad, AvisoGrupo
from aula.services import entregas_pendientes_qs, url_aula_grupo
from campus.services.mensajes import hilos_no_leidos_qs
from sii.identity import docente_para_usuario
from sii.models import ActaFinal, HorarioSlot, Inscripcion
from ventas.models import EdicionCurso


def _curso_ids(user):
    def _ids():
        docente = docente_para_usuario(user)
        if docente is None:
            return []
        return list(docente.cursos_asignados.values_list("curso_id", flat=True))

    return memo_user(user, "curso_ids", _ids)


def _ediciones_asignadas(user):
    ids = _curso_ids(user)
    qs = EdicionCurso.objects.filter(
        id_curso__id_curso_id__in=ids,
        id_curso__id_curso__isnull=False,
    ).select_related("id_curso", "id_curso__id_curso")
    return ids, qs


def _clases_hoy(user, hoy):
    ids = _curso_ids(user)
    qs = (
        HorarioSlot.objects.filter(
            curso_id__in=ids,
            dia=hoy.isoweekday(),
            periodo__fecha_inicio__lte=hoy,
            periodo__fecha_fin__gte=hoy,
        )
        .select_related("curso", "periodo")
        .order_by("hora_inicio")
    )
    count, filas = cola(qs, user)
    items = []
    for slot in filas:
        inicio = slot.hora_inicio.strftime("%H:%M")
        fin = slot.hora_fin.strftime("%H:%M")
        lugar = slot.lugar or "sin lugar"
        items.append(
            Item(
                titulo=f"{inicio}–{fin} · {slot.curso}",
                meta=lugar,
                url=reverse_home("aula_curso", "docente.clases_hoy", args=[slot.curso_id]),
            )
        )
    mensaje = "Aún no tienes grupos asignados. Control escolar te los asigna en Docentes." if not ids else "No tienes clases hoy"
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("aula_dashboard", "docente.clases_hoy"),
        cta_label="Abrir aula",
        mensaje_vacio=mensaje,
    )


def _por_calificar(user, hoy):
    ids = _curso_ids(user)
    qs = entregas_pendientes_qs(user).filter(actividad__curso_id__in=ids)
    request = getattr(user, "_inicio_request", None)
    total_fn = qs.count
    total = memo(request, "pendientes_calificar", total_fn) if request is not None else total_fn()
    agrupado = (
        qs.values("actividad_id", "actividad__nombre", "actividad__curso__nombre")
        .annotate(n=Count("id"), mas_vieja=Min("fecha_entrega"))
        .order_by("mas_vieja")
    )
    items = []
    if not solo_conteo(user):
        for fila in list(agrupado[:5]):
            items.append(
                Item(
                    titulo=f"{fila['actividad__nombre']} · {fila['n']} entregas",
                    meta=fila["actividad__curso__nombre"],
                    url=reverse_home("aula_calificar", "docente.por_calificar", args=[fila["actividad_id"]]),
                    badge=str(fila["n"]),
                    badge_tone="text-bg-warning",
                )
            )
    return WidgetData(
        count=total,
        items=items,
        cta_url=reverse_home("aula_por_calificar", "docente.por_calificar"),
        cta_label="Calificar",
        ver_todos_url=reverse_home("aula_por_calificar", "docente.por_calificar"),
        mensaje_vacio="Nada por calificar",
    )


def _grupos(user, hoy):
    ids, qs = _ediciones_asignadas(user)
    qs = qs.filter(activo=True, estado="en_curso").annotate(
        alumnos=Count("inscripciones_sii", filter=Q(inscripciones_sii__estado="activo"))
    )
    count, filas = cola(qs.order_by("codigo_edicion"), user)
    items = []
    for ed in filas:
        curso_sii = getattr(ed.id_curso, "id_curso", None)
        url = reverse_home("aula_dashboard", "docente.grupos")
        if curso_sii is not None:
            url = with_from_home(url_aula_grupo(curso_sii, ed), "docente.grupos")
        items.append(
            Item(
                titulo=ed.codigo_edicion,
                meta=f"{ed.alumnos} alumnos",
                url=url,
            )
        )
    mensaje = "Aún no tienes grupos asignados. Control escolar te los asigna en Docentes." if not ids else "No hay grupos en curso"
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("aula_dashboard", "docente.grupos"),
        cta_label="Entrar",
        mensaje_vacio=mensaje,
    )


def _cierran(user, hoy):
    ids = _curso_ids(user)
    hasta = hoy + timedelta(days=7)
    roster_sq = (
        Inscripcion.objects.filter(curso_id=OuterRef("curso_id"), estado="activo")
        .values("curso_id")
        .annotate(n=Count("id"))
        .values("n")[:1]
    )
    qs = (
        Actividad.objects.filter(curso_id__in=ids, estado="activa", fecha_limite__range=(hoy, hasta))
        .annotate(
            entregas=Count("calificaciones", filter=Q(calificaciones__entregado=True)),
            roster=Coalesce(Subquery(roster_sq, output_field=IntegerField()), 0),
        )
        .select_related("curso")
        .order_by("fecha_limite")
    )
    if solo_conteo(user):
        count, filas = qs.count(), []
    else:
        filas = list(qs[:5])
        count = qs.count() if len(filas) == 5 else len(filas)
    items = []
    for act in filas:
        dias = (act.fecha_limite - hoy).days
        cierra = "Cierra hoy" if dias == 0 else (f"Cierra en {dias} día" if dias == 1 else f"Cierra en {dias} días")
        items.append(
            Item(
                titulo=act.nombre,
                meta=f"{cierra} · {act.entregas}/{act.roster} entregas",
                url=reverse_home("aula_calificar", "docente.cierran", args=[act.pk]),
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("aula_dashboard", "docente.cierran"),
        cta_label="Ver actividad",
        mensaje_vacio="Nada cierra esta semana",
    )


def _sin_aviso(user, hoy):
    ids, qs = _ediciones_asignadas(user)
    qs = (
        qs.filter(activo=True, estado="en_curso")
        .annotate(tiene_aviso=Exists(AvisoGrupo.objects.filter(publicado=True, edicion=OuterRef("pk"))))
        .filter(tiene_aviso=False)
    )
    count, filas = cola(qs, user)
    items = []
    for ed in filas:
        curso_sii = getattr(ed.id_curso, "id_curso", None)
        url = reverse_home("aula_dashboard", "docente.sin_aviso")
        if curso_sii is not None:
            url = with_from_home(reverse("aula_aviso_grupo", args=[curso_sii.pk, ed.pk]), "docente.sin_aviso")
        items.append(
            Item(
                titulo=ed.codigo_edicion,
                meta="Sin aviso publicado",
                url=url,
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("aula_dashboard", "docente.sin_aviso"),
        cta_label="Publicar aviso",
        mensaje_vacio=(
            "Aún no tienes grupos asignados. Control escolar te los asigna en Docentes."
            if not ids
            else "Todos tus grupos tienen aviso"
        ),
    )


def _mensajes(user, hoy):
    qs = hilos_no_leidos_qs(user)
    count, filas = cola(qs, user)
    items = []
    for hilo in filas:
        items.append(
            Item(
                titulo=hilo.asunto,
                meta="Sin leer",
                url=reverse_home("sii_hilo", "docente.mensajes", args=[hilo.pk]),
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_mensajes", "docente.mensajes"),
        cta_label="Abrir",
        mensaje_vacio="No hay mensajes sin leer",
    )


def _actas(user, hoy):
    ids = _curso_ids(user)
    qs = (
        ActaFinal.objects.filter(
            estado="borrador",
            curso_id__in=ids,
            periodo__fecha_fin__lt=hoy,
            periodo__cerrado=False,
        )
        .select_related("curso", "periodo")
        .order_by("periodo__fecha_fin")
    )
    count, filas = cola(qs, user)
    items = []
    for acta in filas:
        items.append(
            Item(
                titulo=f"{acta.curso} · {acta.periodo}",
                meta="Por publicar",
                url=reverse_home("sii_acta_detalle", "docente.actas", args=[acta.pk]),
            )
        )
    return WidgetData(
        count=count,
        items=items,
        cta_url=reverse_home("sii_actas", "docente.actas"),
        cta_label="Abrir acta",
        mensaje_vacio="No hay actas por publicar",
    )


registrar(Widget("docente.clases_hoy", "Mis clases de hoy", "docente", "sii.horario", 10, "bi-clock", _clases_hoy))
registrar(Widget("docente.por_calificar", "Por calificar", "docente", "aula.calificar", 20, "bi-pencil-square", _por_calificar))
registrar(Widget("docente.grupos", "Mis grupos activos", "docente", "aula.cursos", 30, "bi-people", _grupos))
registrar(Widget("docente.cierran", "Actividades que cierran pronto", "docente", "aula.actividades", 40, "bi-hourglass-split", _cierran))
registrar(Widget("docente.sin_aviso", "Grupos sin aviso", "docente", "aula.actividades", 50, "bi-megaphone", _sin_aviso))
registrar(Widget("docente.mensajes", "Mensajes sin leer", "docente", "sii.mensajes", 60, "bi-chat-dots", _mensajes))
registrar(Widget("docente.actas", "Actas por publicar", "docente", "sii.actas.final.write", 70, "bi-journal-check", _actas))
