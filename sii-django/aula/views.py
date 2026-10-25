from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from aula.forms import (
    ActividadForm,
    AvisoForm,
    CalificacionForm,
    EntregaForm,
    RecursoForm,
    SeccionForm,
)
from aula.models import Actividad, AvisoGrupo, CalificacionActividad, Recurso, SeccionTema
from aula.services import (
    actividades_del_grupo,
    alumno_pertenece_al_grupo,
    actualizar_kardex,
    curso_sii_de_edicion,
    entregas_pendientes_qs,
    inscripcion_en_grupo,
    roster_del_grupo,
    url_aula_grupo,
)
from sii.identity import (
    alumno_para_usuario,
    cursos_visibles,
    docente_para_usuario,
    ediciones_visibles,
    es_administrador,
    puede_gestionar_curso,
    puede_gestionar_edicion,
)
from sii.models import Curso, DocenteCurso, HorarioSlot, Inscripcion
from ventas.models import EdicionCurso


def _puede_gestionar(user, curso):
    return puede_gestionar_curso(user, curso)


def _curso_visible(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if not cursos_visibles(request.user).filter(pk=curso.pk).exists():
        raise Http404()
    return curso


def _edicion_visible(request, edicion_id):
    edicion = get_object_or_404(
        EdicionCurso.objects.select_related("id_curso", "id_curso__id_curso"),
        pk=edicion_id,
    )
    if not ediciones_visibles(request.user).filter(pk=edicion.pk).exists():
        raise Http404()
    return edicion


def _resolver_grupo(request, curso, edicion_id=None):
    visibles = ediciones_visibles(request.user).filter(id_curso__id_curso=curso)
    if edicion_id is not None:
        edicion = _edicion_visible(request, edicion_id)
        if curso_sii_de_edicion(edicion) != curso:
            raise Http404()
        return edicion, visibles
    alumno = alumno_para_usuario(request.user)
    if alumno:
        inscripcion = Inscripcion.de_alumno_en_curso(alumno, curso)
        if inscripcion and inscripcion.id_edicion_id:
            propia = visibles.filter(pk=inscripcion.id_edicion_id).first()
            if propia:
                return propia, visibles
    if visibles.count() == 1:
        return visibles.first(), visibles
    return None, visibles


def _redir_grupo(curso, edicion=None):
    return redirect(url_aula_grupo(curso, edicion))


def _puede_gestionar_algo(user):
    return es_administrador(user) or docente_para_usuario(user) is not None


@login_required
def home(request):
    grupos = list(ediciones_visibles(request.user).order_by("-fecha_inicio", "codigo_edicion"))
    cursos_con_grupo = {
        curso_sii_de_edicion(edicion).pk
        for edicion in grupos
        if curso_sii_de_edicion(edicion) is not None
    }
    cursos_sueltos = cursos_visibles(request.user).order_by("nombre")
    if cursos_con_grupo:
        cursos_sueltos = cursos_sueltos.exclude(pk__in=cursos_con_grupo)
    return render(
        request,
        "aula/home.html",
        {
            "grupos": grupos,
            "cursos": cursos_sueltos,
            "es_propio": not es_administrador(request.user) and docente_para_usuario(request.user) is None,
            "es_docente": _puede_gestionar_algo(request.user),
        },
    )


def _aviso_del_grupo(curso, edicion):
    qs = AvisoGrupo.objects.filter(curso=curso, publicado=True)
    if edicion is not None:
        qs = qs.filter(edicion=edicion)
    else:
        qs = qs.filter(edicion__isnull=True)
    return qs.first()


def _secciones_ui(curso, edicion, actividades_ui):
    secciones = SeccionTema.objects.filter(curso=curso).prefetch_related("recursos")
    if edicion is not None:
        secciones = secciones.filter(edicion=edicion)
    else:
        secciones = secciones.filter(edicion__isnull=True)
    por_seccion = {}
    sueltas = []
    for fila in actividades_ui:
        seccion_id = fila["actividad"].seccion_id
        if seccion_id:
            por_seccion.setdefault(seccion_id, []).append(fila)
        else:
            sueltas.append(fila)
    bloques = []
    for seccion in secciones:
        bloques.append(
            {
                "seccion": seccion,
                "recursos": seccion.recursos.all(),
                "actividades": por_seccion.get(seccion.pk, []),
            }
        )
    return bloques, sueltas


@login_required
def curso_detail(request, curso_id, edicion_id=None):
    curso = _curso_visible(request, curso_id)
    edicion, ediciones = _resolver_grupo(request, curso, edicion_id)
    if edicion_id is None and ediciones.count() > 1 and edicion is None:
        return render(
            request,
            "aula/elegir_grupo.html",
            {"curso": curso, "ediciones": ediciones},
        )
    gestionar = _puede_gestionar(request.user, curso)
    if edicion is not None:
        gestionar = gestionar and puede_gestionar_edicion(request.user, edicion)
        if not gestionar and not ediciones.filter(pk=edicion.pk).exists():
            raise Http404()
    alumno = alumno_para_usuario(request.user)
    inscripcion = inscripcion_en_grupo(alumno, curso, edicion) if alumno else None
    if alumno and not gestionar and not alumno_pertenece_al_grupo(inscripcion, curso, edicion):
        raise Http404()
    entregas = {}
    if inscripcion:
        entregas = {
            fila.actividad_id: fila
            for fila in CalificacionActividad.objects.filter(inscripcion=inscripcion)
        }
    actividades_ui = [
        {"actividad": actividad, "entrega": entregas.get(actividad.pk)}
        for actividad in actividades_del_grupo(curso, edicion)
    ]
    bloques, sueltas = _secciones_ui(curso, edicion, actividades_ui)
    grupos_docente = DocenteCurso.objects.filter(curso=curso).select_related("docente")
    horarios = (
        HorarioSlot.objects.filter(curso=curso).select_related("periodo").order_by("dia", "hora_inicio")
    )
    roster = roster_del_grupo(curso, edicion) if gestionar else []
    return render(
        request,
        "aula/curso.html",
        {
            "curso": curso,
            "edicion": edicion,
            "ediciones": ediciones,
            "actividades_ui": actividades_ui,
            "bloques": bloques,
            "actividades_sueltas": sueltas,
            "aviso": _aviso_del_grupo(curso, edicion),
            "gestionar": gestionar,
            "inscripcion": inscripcion,
            "puede_cursar": bool(inscripcion and inscripcion.puede_cursar and inscripcion.estado == "activo"),
            "grupos": grupos_docente,
            "horarios": horarios,
            "roster": roster,
            "es_admin": es_administrador(request.user),
            "aula_volver": url_aula_grupo(curso, edicion),
        },
    )


def _form_actividad(request, curso, edicion, instance=None):
    return ActividadForm(
        request.POST or None,
        instance=instance,
        curso=curso,
        edicion=edicion,
    )


@login_required
def actividad_nueva(request, curso_id, edicion_id=None):
    curso = _curso_visible(request, curso_id)
    edicion, _ = _resolver_grupo(request, curso, edicion_id)
    if not _puede_gestionar(request.user, curso):
        messages.error(request, "Solo el docente del grupo puede crear actividades.")
        return _redir_grupo(curso, edicion)
    form = _form_actividad(request, curso, edicion)
    if request.method == "POST" and form.is_valid():
        actividad = form.save(commit=False)
        actividad.curso = curso
        actividad.edicion = edicion
        actividad.save()
        messages.success(request, "Actividad publicada.")
        return _redir_grupo(curso, edicion)
    return render(
        request,
        "aula/actividad_form.html",
        {
            "form": form,
            "curso": curso,
            "edicion": edicion,
            "titulo": "Nueva actividad",
            "aula_volver": url_aula_grupo(curso, edicion),
        },
    )


@login_required
def actividad_editar(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not cursos_visibles(request.user).filter(pk=actividad.curso_id).exists():
        raise Http404()
    if not _puede_gestionar(request.user, actividad.curso):
        messages.error(request, "No puedes editar esta actividad.")
        return _redir_grupo(actividad.curso, actividad.edicion)
    form = _form_actividad(request, actividad.curso, actividad.edicion, instance=actividad)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Actividad actualizada.")
        return _redir_grupo(actividad.curso, actividad.edicion)
    return render(
        request,
        "aula/actividad_form.html",
        {
            "form": form,
            "curso": actividad.curso,
            "edicion": actividad.edicion,
            "titulo": "Editar actividad",
            "aula_volver": url_aula_grupo(actividad.curso, actividad.edicion),
        },
    )


@login_required
def actividad_entregar(request, pk):
    actividad = get_object_or_404(Actividad.objects.select_related("curso", "edicion"), pk=pk)
    alumno = alumno_para_usuario(request.user)
    inscripcion = (
        inscripcion_en_grupo(alumno, actividad.curso, actividad.edicion) if alumno else None
    )
    if inscripcion is None or not alumno_pertenece_al_grupo(
        inscripcion, actividad.curso, actividad.edicion
    ):
        messages.error(request, "No estás inscrito en este grupo.")
        return redirect("aula_dashboard")
    if not inscripcion.puede_cursar or inscripcion.estado != "activo":
        messages.error(request, "Tu inscripción está pendiente de pago. No puedes entregar todavía.")
        return _redir_grupo(actividad.curso, actividad.edicion)
    motivo = actividad.motivo_cierre_entrega()
    if motivo:
        messages.error(request, motivo)
        return _redir_grupo(actividad.curso, actividad.edicion)
    registro, _ = CalificacionActividad.objects.get_or_create(
        actividad=actividad, inscripcion=inscripcion
    )
    form = EntregaForm(request.POST or None, request.FILES or None, instance=registro)
    if request.method == "POST" and form.is_valid():
        motivo = actividad.motivo_cierre_entrega()
        if motivo:
            messages.error(request, motivo)
            return _redir_grupo(actividad.curso, actividad.edicion)
        registro = form.save(commit=False)
        registro.entregado = True
        registro.fecha_entrega = timezone.localdate()
        registro.save()
        messages.success(request, "Entrega registrada.")
        return _redir_grupo(actividad.curso, actividad.edicion)
    return render(
        request,
        "aula/entrega.html",
        {
            "form": form,
            "actividad": actividad,
            "registro": registro,
            "aula_volver": url_aula_grupo(actividad.curso, actividad.edicion),
        },
    )


@login_required
def actividad_calificar(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not _puede_gestionar(request.user, actividad.curso):
        messages.error(request, "Solo el docente puede calificar.")
        return _redir_grupo(actividad.curso, actividad.edicion)
    inscritos = roster_del_grupo(actividad.curso, actividad.edicion)
    filas = []
    for inscripcion in inscritos:
        registro, _ = CalificacionActividad.objects.get_or_create(
            actividad=actividad, inscripcion=inscripcion
        )
        filas.append(
            {
                "inscripcion": inscripcion,
                "registro": registro,
                "form": CalificacionForm(prefix=str(inscripcion.pk), instance=registro),
            }
        )
    return render(
        request,
        "aula/calificar.html",
        {
            "actividad": actividad,
            "filas": filas,
            "aula_volver": url_aula_grupo(actividad.curso, actividad.edicion),
        },
    )


@login_required
@require_POST
def actividad_guardar_calificacion(request, pk, inscripcion_id):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not _puede_gestionar(request.user, actividad.curso):
        messages.error(request, "Solo el docente puede calificar.")
        return _redir_grupo(actividad.curso, actividad.edicion)
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id, curso=actividad.curso)
    if actividad.edicion_id and inscripcion.id_edicion_id not in (None, actividad.edicion_id):
        raise Http404()
    registro, _ = CalificacionActividad.objects.get_or_create(
        actividad=actividad, inscripcion=inscripcion
    )
    form = CalificacionForm(request.POST, prefix=str(inscripcion.pk), instance=registro)
    if form.is_valid():
        form.save()
        actualizar_kardex(inscripcion)
        messages.success(request, f"Calificación de {inscripcion.alumno} guardada.")
    else:
        messages.error(request, "Revisa la calificación.")
    return redirect("aula_calificar", pk=actividad.pk)


@login_required
@require_POST
def actividad_guardar_calificaciones(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not _puede_gestionar(request.user, actividad.curso):
        messages.error(request, "Solo el docente puede calificar.")
        return _redir_grupo(actividad.curso, actividad.edicion)
    inscritos = roster_del_grupo(actividad.curso, actividad.edicion)
    guardadas = 0
    for inscripcion in inscritos:
        registro, _ = CalificacionActividad.objects.get_or_create(
            actividad=actividad, inscripcion=inscripcion
        )
        form = CalificacionForm(request.POST, prefix=str(inscripcion.pk), instance=registro)
        if form.is_valid():
            form.save()
            actualizar_kardex(inscripcion)
            guardadas += 1
    if guardadas:
        messages.success(request, f"{guardadas} calificación(es) guardada(s).")
    else:
        messages.error(request, "Revisa las calificaciones.")
    return redirect("aula_calificar", pk=actividad.pk)


@login_required
def por_calificar(request):
    qs = entregas_pendientes_qs(request.user)
    return render(request, "aula/por_calificar.html", {"pendientes": qs})


@login_required
def seccion_nueva(request, curso_id, edicion_id=None):
    curso = _curso_visible(request, curso_id)
    edicion, _ = _resolver_grupo(request, curso, edicion_id)
    if not _puede_gestionar(request.user, curso):
        messages.error(request, "Solo el docente del grupo puede crear secciones.")
        return _redir_grupo(curso, edicion)
    form = SeccionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        seccion = form.save(commit=False)
        seccion.curso = curso
        seccion.edicion = edicion
        seccion.save()
        messages.success(request, "Sección creada.")
        return _redir_grupo(curso, edicion)
    return render(
        request,
        "aula/seccion_form.html",
        {
            "form": form,
            "curso": curso,
            "edicion": edicion,
            "titulo": "Nueva sección",
            "aula_volver": url_aula_grupo(curso, edicion),
        },
    )


@login_required
def seccion_editar(request, pk):
    seccion = get_object_or_404(SeccionTema, pk=pk)
    if not cursos_visibles(request.user).filter(pk=seccion.curso_id).exists():
        raise Http404()
    if not _puede_gestionar(request.user, seccion.curso):
        messages.error(request, "No puedes editar esta sección.")
        return _redir_grupo(seccion.curso, seccion.edicion)
    form = SeccionForm(request.POST or None, instance=seccion)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sección actualizada.")
        return _redir_grupo(seccion.curso, seccion.edicion)
    return render(
        request,
        "aula/seccion_form.html",
        {
            "form": form,
            "curso": seccion.curso,
            "edicion": seccion.edicion,
            "titulo": "Editar sección",
            "aula_volver": url_aula_grupo(seccion.curso, seccion.edicion),
        },
    )


@login_required
def recurso_nuevo(request, pk):
    seccion = get_object_or_404(SeccionTema, pk=pk)
    if not cursos_visibles(request.user).filter(pk=seccion.curso_id).exists():
        raise Http404()
    if not _puede_gestionar(request.user, seccion.curso):
        messages.error(request, "Solo el docente puede publicar materiales.")
        return _redir_grupo(seccion.curso, seccion.edicion)
    form = RecursoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        recurso = form.save(commit=False)
        recurso.seccion = seccion
        recurso.save()
        messages.success(request, "Material publicado.")
        return _redir_grupo(seccion.curso, seccion.edicion)
    return render(
        request,
        "aula/recurso_form.html",
        {
            "form": form,
            "seccion": seccion,
            "curso": seccion.curso,
            "titulo": "Nuevo material",
            "aula_volver": url_aula_grupo(seccion.curso, seccion.edicion),
        },
    )


@login_required
def aviso_editar(request, curso_id, edicion_id=None):
    curso = _curso_visible(request, curso_id)
    edicion, _ = _resolver_grupo(request, curso, edicion_id)
    if not _puede_gestionar(request.user, curso):
        messages.error(request, "Solo el docente puede publicar el aviso del grupo.")
        return _redir_grupo(curso, edicion)
    aviso = AvisoGrupo.objects.filter(curso=curso, edicion=edicion).first()
    form = AvisoForm(request.POST or None, instance=aviso)
    if request.method == "POST" and form.is_valid():
        recado = form.save(commit=False)
        recado.curso = curso
        recado.edicion = edicion
        recado.save()
        messages.success(request, "Aviso del grupo actualizado.")
        return _redir_grupo(curso, edicion)
    return render(
        request,
        "aula/aviso_form.html",
        {
            "form": form,
            "curso": curso,
            "edicion": edicion,
            "titulo": "Aviso del grupo",
            "aula_volver": url_aula_grupo(curso, edicion),
        },
    )
