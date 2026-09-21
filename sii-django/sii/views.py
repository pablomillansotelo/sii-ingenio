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
    HorarioSlotForm,
    InscripcionForm,
    PeriodoForm,
)
from sii.identity import (
    alumno_para_usuario,
    alumnos_visibles,
    cursos_visibles,
    docente_para_usuario,
    es_administrador,
    inscripciones_visibles,
)
from sii.models import Alumno, ActaFinal, Curso, HorarioSlot, Inscripcion, Periodo


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
        alumno = form.save()
        from sii.accounts import provisionar_persona

        cuenta = provisionar_persona(alumno, temporal=True)
        messages.success(request, f"Alumno dado de alta. {cuenta.mensaje()}")
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
        docente = form.save()
        from sii.accounts import provisionar_persona

        cuenta = provisionar_persona(docente, temporal=True)
        messages.success(request, f"Docente dado de alta. {cuenta.mensaje()}")
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


def _alumno_o_404(request, alumno_id):
    alumno = get_object_or_404(alumnos_visibles(request.user), pk=alumno_id)
    return alumno


@login_required
def mi_ficha(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        if es_administrador(request.user):
            return redirect("sii_alumnos")
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("inicio")
    return redirect("sii_alumno_ficha", alumno_id=alumno.pk)


@login_required
def alumno_ficha(request, alumno_id):
    from sii.identity import ventas_visibles

    alumno = _alumno_o_404(request, alumno_id)
    inscripciones = (
        Inscripcion.objects.filter(alumno=alumno)
        .select_related("curso", "periodo", "id_edicion")
        .order_by("-periodo__fecha_inicio")
    )
    horarios = HorarioSlot.objects.filter(
        curso_id__in=inscripciones.values_list("curso_id", flat=True),
        periodo_id__in=inscripciones.values_list("periodo_id", flat=True),
    ).select_related("curso", "periodo")
    ventas = []
    if es_administrador(request.user):
        ventas = list(
            ventas_visibles(request.user)
            .filter(id_cliente__id_alumno_sii=alumno)
            .order_by("-id_venta")[:8]
        )
    user = None
    if alumno.user_id:
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.filter(pk=alumno.user_id).first()
    return render(
        request,
        "sii/alumno_ficha.html",
        {
            "alumno": alumno,
            "inscripciones": inscripciones,
            "horarios": horarios,
            "ventas": ventas,
            "cuenta": user,
            "propia": alumno_para_usuario(request.user) == alumno,
            "puede_operar": es_administrador(request.user),
        },
    )


@login_required
@_solo_admin
@require_POST
def alumno_reset_cuenta(request, alumno_id):
    from sii.accounts import emitir_password_temporal, provisionar_persona

    alumno = get_object_or_404(Alumno, pk=alumno_id)
    cuenta = provisionar_persona(alumno, temporal=False)
    password = emitir_password_temporal(cuenta.user)
    messages.success(
        request,
        f"Nueva contraseña temporal para {cuenta.user.username}: {password}. Cópiala ahora.",
    )
    return redirect("sii_alumno_ficha", alumno_id=alumno.pk)


@login_required
def actas_list(request):
    from sii.actas import acta_de, grupos_de_acta
    from sii.models import Curso

    filas = []
    for par in grupos_de_acta(request.user):
        curso = Curso.objects.filter(pk=par["curso_id"]).first()
        periodo = Periodo.objects.filter(pk=par["periodo_id"]).first()
        if curso is None or periodo is None:
            continue
        acta = acta_de(curso, periodo)
        filas.append({"curso": curso, "periodo": periodo, "acta": acta})
    filas.sort(key=lambda f: (f["periodo"].fecha_inicio, f["curso"].nombre), reverse=True)
    return render(request, "sii/actas.html", {"filas": filas, "puede_operar": es_administrador(request.user)})


@login_required
def acta_detalle(request, acta_id):
    from sii.actas import sincronizar_renglones
    from sii.rbac import has_feature, scope_for

    acta = get_object_or_404(ActaFinal.objects.select_related("curso", "periodo"), pk=acta_id)
    if not has_feature(request.user, "sii.actas"):
        messages.error(request, "No puedes ver actas.")
        return redirect("sii_home")
    if scope_for(request.user, "sii.actas") == "assigned":
        docente = docente_para_usuario(request.user)
        if docente is None or not docente.cursos_asignados.filter(curso=acta.curso).exists():
            messages.error(request, "Esa acta no es de tus grupos.")
            return redirect("sii_actas")
    renglones = sincronizar_renglones(acta)
    return render(
        request,
        "sii/acta_detalle.html",
        {
            "acta": acta,
            "renglones": renglones,
            "congelada": acta.congelada,
            "puede_publicar": not acta.congelada,
        },
    )


@login_required
@require_POST
def acta_publicar(request, acta_id):
    from decimal import Decimal, InvalidOperation

    from sii.actas import publicar_acta
    from sii.rbac import has_feature, scope_for

    acta = get_object_or_404(ActaFinal.objects.select_related("curso", "periodo"), pk=acta_id)
    if not has_feature(request.user, "sii.actas.final.write"):
        messages.error(request, "No puedes publicar actas.")
        return redirect("sii_actas")
    if scope_for(request.user, "sii.actas.final.write") == "assigned":
        docente = docente_para_usuario(request.user)
        if docente is None or not docente.cursos_asignados.filter(curso=acta.curso).exists():
            messages.error(request, "Esa acta no es de tus grupos.")
            return redirect("sii_actas")
    calificaciones = {}
    for key, value in request.POST.items():
        if not key.startswith("calificacion_"):
            continue
        if value in ("", None):
            continue
        try:
            calificaciones[key.split("_", 1)[1]] = Decimal(value)
        except (InvalidOperation, IndexError):
            continue
    try:
        publicar_acta(acta, request.user, calificaciones)
        messages.success(request, "Acta publicada. Las calificaciones quedan como oficiales.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("sii_acta_detalle", acta_id=acta.pk)


@login_required
@_solo_admin
@require_POST
def periodo_cerrar(request):
    from sii.actas import cerrar_periodo

    periodo = get_object_or_404(Periodo, pk=request.POST.get("id"))
    cerrar_periodo(periodo, request.user)
    messages.success(request, f"Periodo {periodo.nombre} cerrado. Las actas quedan congeladas.")
    return redirect("sii_periodos")


def _horarios_visibles(user):
    qs = HorarioSlot.objects.select_related("curso", "periodo")
    if es_administrador(user):
        return qs
    curso_ids = cursos_visibles(user).values_list("pk", flat=True)
    return qs.filter(curso_id__in=curso_ids)


@login_required
def horario_list(request):
    return render(
        request,
        "sii/horario.html",
        {
            "slots": _horarios_visibles(request.user),
            "form_slot": HorarioSlotForm(),
            "puede_operar": es_administrador(request.user),
        },
    )


@login_required
@_solo_admin
@require_POST
def horario_crear(request):
    form = HorarioSlotForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Horario registrado.")
    else:
        messages.error(request, "Revisa curso, periodo y horas.")
    return redirect("sii_horario")


@login_required
@_solo_admin
@require_POST
def horario_quitar(request):
    slot = get_object_or_404(HorarioSlot, pk=request.POST.get("id_slot"))
    slot.delete()
    messages.success(request, "Horario eliminado.")
    return redirect("sii_horario")

