from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from sii.models import Curso, Inscripcion


@login_required
def home(request):
    cursos = Curso.objects.select_related("oferta").order_by("nombre")
    return render(request, "aula/home.html", {"cursos": cursos})


@login_required
def kardex(request):
    inscripciones = Inscripcion.objects.select_related(
        "alumno", "curso", "periodo"
    ).all()
    kardex = [
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
    return render(request, "alumnos/kardex.html", {"kardex": kardex})
