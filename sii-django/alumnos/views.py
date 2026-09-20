from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from sii.models import Inscripcion


@login_required
def home(request):
    return redirect("sii_home")


@login_required
def kardex(request):
    inscripciones = Inscripcion.objects.select_related(
        "alumno", "curso", "periodo"
    ).all()
    kardex = [
        {
            "clave": inscripcion.curso_id,
            "nombre": inscripcion.curso.nombre,
            "alumno": inscripcion.alumno,
            "creditos": "",
            "calificacion": inscripcion.calificacion,
            "periodo": inscripcion.periodo.nombre if inscripcion.periodo_id else "",
        }
        for inscripcion in inscripciones
    ]
    return render(request, "alumnos/kardex.html", {"kardex": kardex})
