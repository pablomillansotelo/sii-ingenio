from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from docente.models import Docente
from sii.models import Alumno, Curso, Inscripcion, Periodo
from ventas.models import Cliente, Producto, Venta


@login_required
def home(request):
    context = {
        "stats": [
            {"label": "Clientes", "value": Cliente.objects.count(), "href": "Clientes"},
            {"label": "Ventas", "value": Venta.objects.count(), "href": "Ventas"},
            {"label": "Alumnos", "value": Alumno.objects.count(), "href": "sii_alumnos"},
            {"label": "Cursos SII", "value": Curso.objects.count(), "href": "sii_cursos"},
            {"label": "Cursos en venta", "value": Producto.objects.count(), "href": "Inventario"},
            {"label": "Inscripciones", "value": Inscripcion.objects.count(), "href": "sii_inscripciones"},
        ],
        "alumnos_recientes": Alumno.objects.order_by("-id")[:5],
        "ventas_recientes": Venta.objects.select_related("id_cliente").order_by("-id_venta")[:5],
    }
    return render(request, "sii/home.html", context)


@login_required
def alumnos_list(request):
    return render(request, "sii/alumnos.html", {"alumnos": Alumno.objects.all().order_by("apellido", "nombre")})


@login_required
def cursos_list(request):
    return render(
        request,
        "sii/cursos.html",
        {"cursos": Curso.objects.select_related("oferta").order_by("nombre")},
    )


@login_required
def inscripciones_list(request):
    inscripciones = Inscripcion.objects.select_related("alumno", "curso", "periodo").all()
    return render(request, "sii/inscripciones.html", {"inscripciones": inscripciones})


@login_required
def periodos_list(request):
    return render(request, "sii/periodos.html", {"periodos": Periodo.objects.all().order_by("-fecha_inicio")})


@login_required
def docentes_list(request):
    return render(request, "sii/docentes.html", {"docentes": Docente.objects.all().order_by("apellido", "nombre")})
