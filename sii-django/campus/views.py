from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from campus.forms import AparienciaForm, FichaAlumnoForm
from campus.hub import CLAVES_VALIDAS, HUB_ACCESOS
from campus.models import CampusFavorito, Noticia
from campus.services.avisos import bandeja_avisos, marcar_leido

from campus.nav import MAS_PROXIMAMENTE, MAS_REALES
from campus.services.calendario import hitos_calendario
from campus.services.cuenta import estado_cuenta
from campus.services.cursos import tarjetas_curso_actual
from campus.services.identidad import identidad_campus
from campus.services.noticias import noticias_publicadas, noticias_publicadas_qs
from campus.services.preferencias import preferencia_de
from campus.services.constancia import construir_constancia, tipos_disponibles
from sii.identity import alumno_para_usuario
from sii.models import DocumentoExpediente, Inscripcion, SolicitudBaja
from sii.services.expediente import resumen_tipos, validar_archivo
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
        "campus_pref": preferencia_de(request.user),
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
                "cuenta": estado_cuenta(request.user),
                "noticias": list(noticias_publicadas()),
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
@requiere_feature("campus.configuracion")
def configuracion(request):
    pref = preferencia_de(request.user)
    form = AparienciaForm(request.POST or None, instance=pref)
    if request.method == "POST":
        if form.is_valid():
            guardada = form.save(commit=False)
            guardada.user_id = request.user.pk
            guardada.save()
            messages.success(request, "Tus preferencias de apariencia se guardaron.")
            return redirect("campus_configuracion")
        messages.error(request, "Revisa las opciones de apariencia.")
    return render(
        request,
        "campus/configuracion.html",
        _ctx(request, "mas", {"form": form, "campus_pref": preferencia_de(request.user)}),
    )


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


@login_required
@requiere_feature("campus.kardex")
def kardex(request):
    from sii.identity import inscripciones_visibles
    from sii.views import _kardex_rows

    inscripciones = inscripciones_visibles(request.user).order_by(
        "-periodo__fecha_inicio", "curso__nombre"
    )
    return render(
        request,
        "campus/kardex.html",
        _ctx(request, "control", {"kardex": _kardex_rows(inscripciones)}),
    )


@login_required
@requiere_feature("campus.estado_cuenta")
def estado_cuenta_view(request):
    return render(
        request,
        "campus/estado_cuenta.html",
        _ctx(request, "control", {"cuenta": estado_cuenta(request.user)}),
    )


@login_required
@requiere_feature("campus.noticias")
def noticia_detalle(request, noticia_id):
    noticia = get_object_or_404(noticias_publicadas_qs(), pk=noticia_id)
    return render(request, "campus/noticia.html", _ctx(request, "inicio", {"noticia": noticia}))


@login_required
@requiere_feature("campus.constancias")
def constancias(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    return render(
        request,
        "campus/constancias.html",
        _ctx(
            request,
            "control",
            {"alumno": alumno, "tipos": tipos_disponibles(alumno)},
        ),
    )


@login_required
@requiere_feature("campus.constancias")
def constancia_pdf(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    tipo = request.GET.get("tipo") or "historial"
    pdf_bytes, tipo_real = construir_constancia(alumno, tipo)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="constancia-{tipo_real}-{alumno.pk}.pdf"'
    return response


@login_required
@requiere_feature("campus.bajas")
def bajas(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    activas = (
        Inscripcion.objects.filter(alumno=alumno, estado="activo")
        .select_related("curso", "periodo")
        .order_by("curso__nombre")
    )
    if request.method == "POST":
        motivo = (request.POST.get("motivo") or "").strip()
        ins = get_object_or_404(
            Inscripcion, pk=request.POST.get("inscripcion_id"), alumno=alumno, estado="activo"
        )
        if not motivo:
            messages.error(request, "El motivo es obligatorio.")
        elif SolicitudBaja.objects.filter(inscripcion=ins, estado=SolicitudBaja.ESTADO_ENVIADA).exists():
            messages.error(request, "Ya hay una solicitud pendiente para esa inscripción.")
        else:
            SolicitudBaja.objects.create(
                inscripcion=ins,
                alumno=alumno,
                motivo=motivo,
                creada_por_id=request.user.pk,
            )
            messages.success(request, "Solicitud enviada. Control escolar debe aprobarla para aplicar la baja.")
            return redirect("campus_bajas")
    solicitudes = (
        SolicitudBaja.objects.filter(alumno=alumno)
        .select_related("inscripcion__curso", "inscripcion__periodo")
    )
    return render(
        request,
        "campus/bajas.html",
        _ctx(request, "control", {"activas": activas, "solicitudes": solicitudes}),
    )


@login_required
@requiere_feature("campus.expediente")
def expediente(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    if request.method == "POST":
        tipo = request.POST.get("tipo")
        archivo = request.FILES.get("archivo")
        tipos_ok = {c[0] for c in DocumentoExpediente.TIPO_CHOICES}
        if tipo not in tipos_ok or archivo is None:
            messages.error(request, "Indica el tipo y el archivo.")
        elif DocumentoExpediente.objects.filter(
            alumno=alumno, tipo=tipo, estado=DocumentoExpediente.ESTADO_ACEPTADO
        ).exists():
            messages.error(request, "Ese documento ya fue aceptado y no se reemplaza desde aquí.")
        else:
            try:
                validar_archivo(archivo)
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                DocumentoExpediente.objects.create(
                    alumno=alumno,
                    tipo=tipo,
                    archivo=archivo,
                    subido_por_id=request.user.pk,
                )
                messages.success(request, "Documento enviado a revisión.")
                return redirect("campus_expediente")
    return render(
        request,
        "campus/expediente.html",
        _ctx(request, "control", {"filas": resumen_tipos(alumno)}),
    )


@login_required
@requiere_feature("campus.expediente")
def expediente_archivo(request, pk):
    alumno = alumno_para_usuario(request.user)
    doc = get_object_or_404(DocumentoExpediente, pk=pk, alumno=alumno)
    if not doc.archivo:
        raise Http404()
    return FileResponse(doc.archivo.open("rb"), as_attachment=True, filename=doc.archivo.name.split("/")[-1])
