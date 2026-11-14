from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from campus.forms import FichaAlumnoForm

from campus.nav import MAS_PROXIMAMENTE, MAS_REALES
from campus.services.calendario import hitos_calendario
from campus.services.cursos import tarjetas_curso_actual
from campus.services.identidad import identidad_campus
from sii.identity import alumno_para_usuario
from sii.rbac import requiere_feature
from sii.services.avance import avance_academico


def _ctx(request, tab, extra=None):
    alumno = alumno_para_usuario(request.user)
    ctx = {
        "campus_tab": tab,
        "campus_alumno": alumno,
        "campus_identidad": identidad_campus(request.user, alumno),
        "mas_reales": MAS_REALES,
        "mas_proximamente": MAS_PROXIMAMENTE,
    }
    if extra:
        ctx.update(extra)
    return ctx


@login_required
@requiere_feature("campus.inicio")
def inicio(request):
    alumno = alumno_para_usuario(request.user)
    cursos = tarjetas_curso_actual(alumno)
    return render(
        request,
        "campus/inicio.html",
        _ctx(
            request,
            "inicio",
            {
                "avance": avance_academico(alumno),
                "cursos_actuales": cursos["tarjetas"],
                "periodo_actual": cursos["periodo"],
            },
        ),
    )


@login_required
@requiere_feature("campus.control_escolar")
def control_escolar(request):
    return render(request, "campus/control_escolar.html", _ctx(request, "control"))


@login_required
@requiere_feature("campus.calendario")
def calendario(request):
    alumno = alumno_para_usuario(request.user)
    return render(
        request,
        "campus/calendario.html",
        _ctx(request, "calendario", hitos_calendario(alumno)),
    )


@login_required
@requiere_feature("campus.inicio")
def mensajes(request):
    return render(request, "campus/mensajes.html", _ctx(request, "mensajes"))


@login_required
@requiere_feature("campus.inicio")
def mas(request):
    return render(request, "campus/mas.html", _ctx(request, "mas"))


@login_required
@requiere_feature("campus.inicio")
def ficha(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    form = FichaAlumnoForm(request.POST or None, instance=alumno)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos de contacto se guardaron en el expediente.")
            return redirect("campus_ficha")
        messages.error(request, "Revisa el teléfono y el código postal.")
    return render(request, "campus/ficha.html", _ctx(request, "mas", {"form": form, "alumno": alumno}))
