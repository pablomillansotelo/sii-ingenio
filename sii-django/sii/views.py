from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from docente.models import Docente, DocenteCurso
from sii.forms import (
    AlumnoForm,
    AsignacionForm,
    CursoForm,
    DocenteForm,
    EditarAlumnoForm,
    EditarCursoForm,
    EditarDocenteForm,
    EditarPeriodoForm,
    InscripcionForm,
    PeriodoForm,
)
from sii.identity import (
    alumnos_visibles,
    cursos_visibles,
    docente_para_usuario,
    es_administrador,
    inscripciones_visibles,
)
from sii.models import Alumno, Curso, Inscripcion, Periodo


def _solo_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not es_administrador(request.user):
            messages.error(request, "Solo control escolar puede hacer esa operación.")
            return redirect("sii_home")
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
def home(request):
    alumnos = alumnos_visibles(request.user)
    cursos = cursos_visibles(request.user)
    inscripciones = inscripciones_visibles(request.user)
    docentes = Docente.objects.all()
    if not es_administrador(request.user):
        propio = docente_para_usuario(request.user)
        docentes = docentes.filter(pk=propio.pk) if propio else docentes.none()
    stats = [
        {"label": "Alumnos", "value": alumnos.count(), "href": "sii_alumnos"},
        {"label": "Cursos", "value": cursos.count(), "href": "sii_cursos"},
        {"label": "Periodos", "value": Periodo.objects.count(), "href": "sii_periodos"},
        {"label": "Inscripciones", "value": inscripciones.count(), "href": "sii_inscripciones"},
        {"label": "Docentes", "value": docentes.count(), "href": "sii_docentes"},
    ]
    return render(
        request,
        "sii/home.html",
        {
            "stats": stats,
            "alumnos_recientes": alumnos.order_by("-id")[:5],
            "puede_operar": es_administrador(request.user),
        },
    )


def _kardex_rows(inscripciones):
    return [
        {
            "clave": inscripcion.curso_id,
            "nombre": inscripcion.curso.nombre,
            "edicion": inscripcion.id_edicion.codigo_edicion if inscripcion.id_edicion_id else "",
            "creditos": "",
            "calificacion": inscripcion.calificacion,
            "periodo": inscripcion.periodo.nombre if inscripcion.periodo_id else "",
            "alumno": inscripcion.alumno,
        }
        for inscripcion in inscripciones.select_related("alumno", "curso", "periodo", "id_edicion")
    ]


@login_required
def kardex(request):
    inscripciones = inscripciones_visibles(request.user)
    mostrar_alumno = es_administrador(request.user) or docente_para_usuario(request.user) is not None
    return render(
        request,
        "alumnos/kardex.html",
        {"kardex": _kardex_rows(inscripciones), "mostrar_alumno": mostrar_alumno},
    )


@login_required
def alumnos_list(request):
    return render(
        request,
        "sii/alumnos.html",
        {
            "alumnos": alumnos_visibles(request.user).order_by("apellido", "nombre"),
            "form_alumno": AlumnoForm(),
            "form_editar_alumno": EditarAlumnoForm(),
            "puede_operar": es_administrador(request.user),
        },
    )


@login_required
def cursos_list(request):
    return render(
        request,
        "sii/cursos.html",
        {
            "cursos": cursos_visibles(request.user).order_by("nombre"),
            "form_curso": CursoForm(),
            "form_editar_curso": EditarCursoForm(),
            "puede_operar": es_administrador(request.user),
        },
    )


@login_required
def inscripciones_list(request):
    return render(
        request,
        "sii/inscripciones.html",
        {
            "inscripciones": inscripciones_visibles(request.user),
            "form_inscripcion": InscripcionForm(),
            "puede_operar": es_administrador(request.user),
        },
    )


@login_required
def periodos_list(request):
    return render(
        request,
        "sii/periodos.html",
        {
            "periodos": Periodo.objects.all().order_by("-fecha_inicio"),
            "form_periodo": PeriodoForm(),
            "form_editar_periodo": EditarPeriodoForm(),
            "puede_operar": es_administrador(request.user),
        },
    )


@login_required
def docentes_list(request):
    docentes = Docente.objects.all().order_by("apellido", "nombre")
    if not es_administrador(request.user):
        propio = docente_para_usuario(request.user)
        docentes = docentes.filter(pk=propio.pk) if propio else docentes.none()
    asignaciones = DocenteCurso.objects.select_related("docente", "curso").order_by("curso__nombre")
    if not es_administrador(request.user):
        propio = docente_para_usuario(request.user)
        asignaciones = asignaciones.filter(docente=propio) if propio else asignaciones.none()
    return render(
        request,
        "sii/docentes.html",
        {
            "docentes": docentes,
            "asignaciones": asignaciones,
            "form_docente": DocenteForm(),
            "form_editar_docente": EditarDocenteForm(),
            "form_asignacion": AsignacionForm(),
            "puede_operar": es_administrador(request.user),
        },
    )


@login_required
@_solo_admin
@require_POST
def alumno_crear(request):
    form = AlumnoForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Alumno dado de alta.")
    else:
        messages.error(request, "Revisa los datos del alumno.")
    return redirect("sii_alumnos")


@login_required
@_solo_admin
@require_POST
def alumno_editar(request):
    alumno = get_object_or_404(Alumno, pk=request.POST.get("id"))
    form = EditarAlumnoForm(request.POST, instance=alumno)
    if form.is_valid():
        form.save()
        messages.success(request, "Alumno actualizado.")
    else:
        messages.error(request, "Revisa los datos del alumno.")
    return redirect("sii_alumnos")


@login_required
@_solo_admin
@require_POST
def periodo_crear(request):
    form = PeriodoForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Periodo creado.")
    else:
        messages.error(request, "Revisa las fechas del periodo.")
    return redirect("sii_periodos")


@login_required
@_solo_admin
@require_POST
def periodo_editar(request):
    periodo = get_object_or_404(Periodo, pk=request.POST.get("id"))
    form = EditarPeriodoForm(request.POST, instance=periodo)
    if form.is_valid():
        form.save()
        messages.success(request, "Periodo actualizado.")
    else:
        messages.error(request, "Revisa las fechas del periodo.")
    return redirect("sii_periodos")


@login_required
@_solo_admin
@require_POST
def curso_crear(request):
    form = CursoForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Curso académico creado.")
    else:
        messages.error(request, "Revisa el nombre del curso.")
    return redirect("sii_cursos")


@login_required
@_solo_admin
@require_POST
def curso_editar(request):
    curso = get_object_or_404(Curso, pk=request.POST.get("id"))
    form = EditarCursoForm(request.POST, instance=curso)
    if form.is_valid():
        form.save()
        messages.success(request, "Curso actualizado.")
    else:
        messages.error(request, "Revisa los datos del curso.")
    return redirect("sii_cursos")


@login_required
@_solo_admin
@require_POST
def docente_crear(request):
    form = DocenteForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Docente dado de alta.")
    else:
        messages.error(request, "Revisa los datos del docente.")
    return redirect("sii_docentes")


@login_required
@_solo_admin
@require_POST
def docente_editar(request):
    docente = get_object_or_404(Docente, pk=request.POST.get("id"))
    form = EditarDocenteForm(request.POST, instance=docente)
    if form.is_valid():
        form.save()
        messages.success(request, "Docente actualizado.")
    else:
        messages.error(request, "Revisa los datos del docente.")
    return redirect("sii_docentes")


@login_required
@_solo_admin
@require_POST
def asignacion_crear(request):
    form = AsignacionForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Docente asignado al curso.")
    else:
        messages.error(request, "Esa asignación ya existe o faltan datos.")
    return redirect("sii_docentes")


@login_required
@_solo_admin
@require_POST
def asignacion_quitar(request):
    asignacion = get_object_or_404(DocenteCurso, pk=request.POST.get("id_asignacion"))
    asignacion.delete()
    messages.success(request, "Asignación eliminada.")
    return redirect("sii_docentes")


@login_required
@_solo_admin
@require_POST
def inscripcion_crear(request):
    form = InscripcionForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Inscripción registrada.")
        return redirect("sii_inscripciones")
    alumno = request.POST.get("alumno")
    curso = request.POST.get("curso")
    periodo = request.POST.get("periodo")
    if alumno and curso and periodo and Inscripcion.objects.filter(
        alumno_id=alumno, curso_id=curso, periodo_id=periodo
    ).exists():
        messages.error(request, "Ese alumno ya tiene este curso en el periodo. Usa reintento si estaba de baja.")
    else:
        messages.error(request, "Revisa alumno, curso y periodo.")
    return redirect("sii_inscripciones")


@login_required
@_solo_admin
@require_POST
def inscripcion_baja(request):
    inscripcion = get_object_or_404(Inscripcion, pk=request.POST.get("id_inscripcion"))
    try:
        inscripcion.dar_baja()
        messages.success(request, "Inscripción dada de baja.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("sii_inscripciones")


@login_required
@_solo_admin
@require_POST
def inscripcion_reintento(request):
    inscripcion = get_object_or_404(Inscripcion, pk=request.POST.get("id_inscripcion"))
    try:
        inscripcion.reintentar()
        messages.success(request, f"Reintento {inscripcion.intento} activo.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("sii_inscripciones")
