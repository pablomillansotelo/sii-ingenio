from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from sii.identity import cursos_visibles, docente_para_usuario, es_administrador, inscripciones_visibles


def _kardex_rows(inscripciones):
    return [
        {
            "clave": inscripcion.curso_id,
            "nombre": inscripcion.curso.nombre,
            "creditos": "",
            "calificacion": inscripcion.calificacion,
            "periodo": inscripcion.periodo.nombre if inscripcion.periodo_id else "",
            "alumno": inscripcion.alumno,
        }
        for inscripcion in inscripciones
    ]


def _inscripciones_visibles(request):
    return inscripciones_visibles(request.user)


@login_required
def home(request):
    return render(
        request,
        "aula/home.html",
        {
            "cursos": cursos_visibles(request.user).order_by("nombre"),
            "es_propio": not es_administrador(request.user) and docente_para_usuario(request.user) is None,
        },
    )


@login_required
def kardex(request):
    inscripciones = inscripciones_visibles(request.user)
    mostrar_alumno = es_administrador(request.user) or docente_para_usuario(request.user) is not None
    return render(
        request,
        "alumnos/kardex.html",
        {"kardex": _kardex_rows(inscripciones), "mostrar_alumno": mostrar_alumno},
    )
