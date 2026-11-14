from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from campus.nav import MAS_PROXIMAMENTE, MAS_REALES
from sii.identity import alumno_para_usuario
from sii.rbac import requiere_feature
from sii.services.avance import avance_academico


def _ctx(request, tab, extra=None):
    ctx = {
        "campus_tab": tab,
        "campus_alumno": alumno_para_usuario(request.user),
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
    return render(
        request,
        "campus/inicio.html",
        _ctx(request, "inicio", {"avance": avance_academico(alumno)}),
    )


@login_required
@requiere_feature("campus.control_escolar")
def control_escolar(request):
    return render(request, "campus/control_escolar.html", _ctx(request, "control"))


@login_required
@requiere_feature("campus.calendario")
def calendario(request):
    return render(request, "campus/calendario.html", _ctx(request, "calendario"))


@login_required
@requiere_feature("campus.inicio")
def mensajes(request):
    return render(request, "campus/mensajes.html", _ctx(request, "mensajes"))


@login_required
@requiere_feature("campus.inicio")
def mas(request):
    return render(request, "campus/mas.html", _ctx(request, "mas"))
