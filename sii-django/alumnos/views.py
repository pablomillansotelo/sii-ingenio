from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from aula.views import _inscripciones_visibles, _kardex_rows
from sii.identity import docente_para_usuario, es_administrador


@login_required
def home(request):
    return redirect("sii_home")


@login_required
def kardex(request):
    inscripciones = _inscripciones_visibles(request)
    mostrar_alumno = es_administrador(request.user) or docente_para_usuario(request.user) is not None
    return render(
        request,
        "alumnos/kardex.html",
        {"kardex": _kardex_rows(inscripciones), "mostrar_alumno": mostrar_alumno},
    )
