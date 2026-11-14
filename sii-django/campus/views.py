from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from campus.forms import FichaAlumnoForm
from campus.hub import CLAVES_VALIDAS, HUB_ACCESOS
from campus.models import CampusFavorito
from campus.services.avisos import bandeja_avisos, marcar_leido

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
    avisos = bandeja_avisos(alumno, filtro="no_leidos")
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
                "avisos_importantes": avisos["importantes_pendientes"],
            },
        ),
    )


@login_required
@requiere_feature("campus.control_escolar")
def control_escolar(request):
    favoritos = set(
        CampusFavorito.objects.filter(user_id=request.user.pk).values_list("clave", flat=True)
    )
    tiles = []
    for item in HUB_ACCESOS:
        tiles.append({**item, "favorito": item["clave"] in favoritos})
    tiles.sort(key=lambda t: (not t["favorito"], t["label"]))
    return render(request, "campus/control_escolar.html", _ctx(request, "control", {"tiles": tiles}))


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


@login_required
@requiere_feature("campus.avisos")
def avisos(request):
    alumno = alumno_para_usuario(request.user)
    filtro = request.GET.get("estado") or "todos"
    if filtro not in ("todos", "leidos", "no_leidos"):
        filtro = "todos"
    data = bandeja_avisos(alumno, filtro=None if filtro == "todos" else filtro)
    return render(
        request,
        "campus/avisos.html",
        _ctx(request, "mas", {"bandeja": data["items"], "filtro": filtro}),
    )


@login_required
@require_POST
@requiere_feature("campus.avisos")
def aviso_leer(request, aviso_id):
    alumno = alumno_para_usuario(request.user)
    aviso = get_object_or_404(avisos_vigentes_qs_safe(alumno), pk=aviso_id)
    marcar_leido(alumno, aviso)
    messages.success(request, "Aviso marcado como leído.")
    return redirect(request.POST.get("next") or "campus_avisos")


def avisos_vigentes_qs_safe(alumno):
    from campus.services.avisos import avisos_vigentes_qs

    return avisos_vigentes_qs(alumno)


@login_required
@require_POST
@requiere_feature("campus.control_escolar")
def favorito_toggle(request):
    clave = request.POST.get("clave")
    if clave not in CLAVES_VALIDAS:
        messages.error(request, "Ese acceso no existe.")
        return redirect("campus_control_escolar")
    existente = CampusFavorito.objects.filter(user_id=request.user.pk, clave=clave).first()
    if existente:
        existente.delete()
    else:
        CampusFavorito.objects.create(user_id=request.user.pk, clave=clave)
    return redirect("campus_control_escolar")
