from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from docente.models import Docente
from sii.identity import (
    alumnos_visibles,
    cursos_visibles,
    docente_para_usuario,
    es_administrador,
    inscripciones_visibles,
    puede_ver_modulo,
)
from sii.models import Periodo
from ventas.models import Cliente, Producto, Venta


@login_required
def home(request):
    alumnos = alumnos_visibles(request.user)
    cursos = cursos_visibles(request.user)
    inscripciones = inscripciones_visibles(request.user)
    stats = [
        {"label": "Alumnos", "value": alumnos.count(), "href": "sii_alumnos"},
        {"label": "Cursos SII", "value": cursos.count(), "href": "sii_cursos"},
        {"label": "Inscripciones", "value": inscripciones.count(), "href": "sii_inscripciones"},
    ]
    ventas_recientes = []
    if puede_ver_modulo(request.user, "ventas"):
        stats = [
            {"label": "Clientes", "value": Cliente.objects.count(), "href": "Clientes"},
            {"label": "Ventas", "value": Venta.objects.count(), "href": "Ventas"},
            {"label": "Cursos en venta", "value": Producto.objects.count(), "href": "Inventario"},
        ] + stats
        ventas_recientes = Venta.objects.select_related("id_cliente").order_by("-id_venta")[:5]
    return render(
        request,
        "sii/home.html",
        {
            "stats": stats,
            "alumnos_recientes": alumnos.order_by("-id")[:5],
            "ventas_recientes": ventas_recientes,
        },
    )


@login_required
def alumnos_list(request):
    return render(
        request,
        "sii/alumnos.html",
        {"alumnos": alumnos_visibles(request.user).order_by("apellido", "nombre")},
    )


@login_required
def cursos_list(request):
    return render(
        request,
        "sii/cursos.html",
        {"cursos": cursos_visibles(request.user).order_by("nombre")},
    )


@login_required
def inscripciones_list(request):
    return render(
        request,
        "sii/inscripciones.html",
        {"inscripciones": inscripciones_visibles(request.user)},
    )


@login_required
def periodos_list(request):
    return render(request, "sii/periodos.html", {"periodos": Periodo.objects.all().order_by("-fecha_inicio")})


@login_required
def docentes_list(request):
    docentes = Docente.objects.all().order_by("apellido", "nombre")
    if not es_administrador(request.user):
        propio = docente_para_usuario(request.user)
        docentes = docentes.filter(pk=propio.pk) if propio else docentes.none()
    return render(request, "sii/docentes.html", {"docentes": docentes})
