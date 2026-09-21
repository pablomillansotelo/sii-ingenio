from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from aula.forms import ActividadForm, CalificacionForm, EntregaForm
from aula.models import Actividad, CalificacionActividad
from aula.services import actualizar_kardex
from docente.models import DocenteCurso
from sii.identity import (
    alumno_para_usuario,
    cursos_visibles,
    docente_para_usuario,
    es_administrador,
)
from sii.models import Curso, HorarioSlot, Inscripcion


def _puede_gestionar(user, curso):
    if es_administrador(user):
        return True
    docente = docente_para_usuario(user)
    if docente is None:
        return False
    return docente.cursos_asignados.filter(curso=curso).exists()


def _curso_visible(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if not cursos_visibles(request.user).filter(pk=curso.pk).exists():
        raise Http404()
    return curso


@login_required
def home(request):
    return render(
        request,
        "aula/home.html",
        {
            "cursos": cursos_visibles(request.user).order_by("nombre"),
            "es_propio": not es_administrador(request.user) and docente_para_usuario(request.user) is None,
            "es_docente": _puede_gestionar_algo(request.user),
        },
    )


def _puede_gestionar_algo(user):
    return es_administrador(user) or docente_para_usuario(user) is not None


@login_required
def curso_detail(request, curso_id):
    curso = _curso_visible(request, curso_id)
    gestionar = _puede_gestionar(request.user, curso)
    alumno = alumno_para_usuario(request.user)
    inscripcion = Inscripcion.de_alumno_en_curso(alumno, curso) if alumno else None
    entregas = {}
    if inscripcion:
        entregas = {
            fila.actividad_id: fila
            for fila in CalificacionActividad.objects.filter(inscripcion=inscripcion)
        }
    actividades_ui = [
        {"actividad": actividad, "entrega": entregas.get(actividad.pk)}
        for actividad in curso.actividades.all()
    ]
    grupos = DocenteCurso.objects.filter(curso=curso).select_related("docente")
    horarios = HorarioSlot.objects.filter(curso=curso).select_related("periodo").order_by("dia", "hora_inicio")
    return render(
        request,
        "aula/curso.html",
        {
            "curso": curso,
            "actividades_ui": actividades_ui,
            "gestionar": gestionar,
            "inscripcion": inscripcion,
            "puede_cursar": bool(inscripcion and inscripcion.puede_cursar and inscripcion.estado == "activo"),
            "grupos": grupos,
            "horarios": horarios,
            "es_admin": es_administrador(request.user),
        },
    )


@login_required
def actividad_nueva(request, curso_id):
    curso = _curso_visible(request, curso_id)
    if not _puede_gestionar(request.user, curso):
        messages.error(request, "Solo el docente del grupo puede crear actividades.")
        return redirect("aula_curso", curso_id=curso.pk)
    form = ActividadForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        actividad = form.save(commit=False)
        actividad.curso = curso
        actividad.save()
        messages.success(request, "Actividad publicada.")
        return redirect("aula_curso", curso_id=curso.pk)
    return render(
        request,
        "aula/actividad_form.html",
        {"form": form, "curso": curso, "titulo": "Nueva actividad"},
    )


@login_required
def actividad_editar(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not cursos_visibles(request.user).filter(pk=actividad.curso_id).exists():
        raise Http404()
    if not _puede_gestionar(request.user, actividad.curso):
        messages.error(request, "No puedes editar esta actividad.")
        return redirect("aula_curso", curso_id=actividad.curso_id)
    form = ActividadForm(request.POST or None, instance=actividad)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Actividad actualizada.")
        return redirect("aula_curso", curso_id=actividad.curso_id)
    return render(
        request,
        "aula/actividad_form.html",
        {"form": form, "curso": actividad.curso, "titulo": "Editar actividad"},
    )


@login_required
def actividad_entregar(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    alumno = alumno_para_usuario(request.user)
    inscripcion = (
        Inscripcion.de_alumno_en_curso(alumno, actividad.curso) if alumno else None
    )
    if inscripcion is None:
        messages.error(request, "No estás inscrito en este curso.")
        return redirect("aula_dashboard")
    if not inscripcion.puede_cursar or inscripcion.estado != "activo":
        messages.error(request, "Tu inscripción está pendiente de pago. No puedes entregar todavía.")
        return redirect("aula_curso", curso_id=actividad.curso_id)
    registro, _ = CalificacionActividad.objects.get_or_create(
        actividad=actividad, inscripcion=inscripcion
    )
    form = EntregaForm(request.POST or None, request.FILES or None, instance=registro)
    if request.method == "POST" and form.is_valid():
        registro = form.save(commit=False)
        registro.entregado = True
        registro.fecha_entrega = timezone.localdate()
        registro.save()
        messages.success(request, "Entrega registrada.")
        return redirect("aula_curso", curso_id=actividad.curso_id)
    return render(
        request,
        "aula/entrega.html",
        {"form": form, "actividad": actividad, "registro": registro},
    )


@login_required
def actividad_calificar(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not _puede_gestionar(request.user, actividad.curso):
        messages.error(request, "Solo el docente puede calificar.")
        return redirect("aula_curso", curso_id=actividad.curso_id)
    inscritos = Inscripcion.objects.filter(curso=actividad.curso, estado="activo").select_related("alumno")
    filas = []
    for inscripcion in inscritos:
        registro, _ = CalificacionActividad.objects.get_or_create(
            actividad=actividad, inscripcion=inscripcion
        )
        filas.append({"inscripcion": inscripcion, "registro": registro, "form": CalificacionForm(prefix=str(inscripcion.pk), instance=registro)})
    return render(
        request,
        "aula/calificar.html",
        {"actividad": actividad, "filas": filas},
    )


@login_required
@require_POST
def actividad_guardar_calificacion(request, pk, inscripcion_id):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not _puede_gestionar(request.user, actividad.curso):
        messages.error(request, "Solo el docente puede calificar.")
        return redirect("aula_curso", curso_id=actividad.curso_id)
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_id, curso=actividad.curso)
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
        return redirect("aula_curso", curso_id=actividad.curso_id)
    inscritos = Inscripcion.objects.filter(curso=actividad.curso, estado="activo")
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
    qs = CalificacionActividad.objects.filter(
        entregado=True, calificacion__isnull=True
    ).select_related("actividad__curso", "inscripcion__alumno")
    if not es_administrador(request.user):
        docente = docente_para_usuario(request.user)
        if docente is None:
            qs = qs.none()
        else:
            qs = qs.filter(
                actividad__curso_id__in=docente.cursos_asignados.values_list("curso_id", flat=True)
            )
    return render(request, "aula/por_calificar.html", {"pendientes": qs})
