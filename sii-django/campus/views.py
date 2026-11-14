from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from campus.forms import AparienciaForm, DatosFiscalesForm, FichaAlumnoForm
from campus.hub import CLAVES_VALIDAS, HUB_ACCESOS
from campus.models import CampusFavorito, ContactoDirectorio, DocumentoNormativa, Hilo, Noticia, TicketAyuda, TicketRespuesta
from campus.services.ayuda import puede_transitar
from campus.services.avisos import bandeja_avisos, marcar_leido

from campus.nav import MAS_PROXIMAMENTE, MAS_REALES
from campus.services.calendario import hitos_calendario
from campus.services.cuenta import estado_cuenta
from campus.services.cursos import tarjetas_curso_actual
from campus.services.identidad import identidad_campus
from campus.services.noticias import noticias_publicadas, noticias_publicadas_qs
from campus.services.preferencias import preferencia_de
from campus.services.mensajes import destinos_alumno, marcar_hilo_leido, no_leidos, abrir_hilo, puede_ver, responder, resumen_hilos
from campus.services.notificaciones import lista as lista_notif, marcar_todas, marcar_una, no_leidas as notif_no_leidas, sincronizar as sync_notif
from campus.services.ludico import perfil_de, ranking as ranking_ludico
from campus.services.retos import sincronizar_retos
from campus.services.constancia import construir_constancia, tipos_disponibles
from campus.services.aceptacion import carga_del_periodo, ventana_abierta
from campus.services.credencial import ficha_credencial
from campus.services.fiscal import cliente_de_alumno
from sii.identity import alumno_para_usuario
from sii.models import AceptacionCarga, DocumentoExpediente, Inscripcion, SolicitudBaja
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
        "campus_mensajes_nuevos": no_leidos(request.user),
        "campus_notif_nuevas": notif_no_leidas(request.user),
        "campus_ludico": perfil_de(alumno),
    }
    if extra:
        ctx.update(extra)
    return ctx


@login_required
@requiere_feature("campus.inicio")
def inicio(request):
    alumno = alumno_para_usuario(request.user)
    sync_notif(request.user, alumno)
    retos = sincronizar_retos(alumno)
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
                "retos": retos,
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
    alumno = alumno_para_usuario(request.user)
    if request.method == "POST":
        try:
            hilo = abrir_hilo(
                request.user,
                request.POST.get("asunto"),
                request.POST.get("cuerpo"),
                request.POST.get("destino"),
                request.FILES.get("archivo"),
            )
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Mensaje enviado.")
            return redirect("campus_hilo", pk=hilo.pk)
    return render(
        request,
        "campus/mensajes.html",
        _ctx(
            request,
            "mensajes",
            {"hilos": resumen_hilos(request.user), "destinos": destinos_alumno(alumno)},
        ),
    )


@login_required
@requiere_feature("campus.mensajes")
def hilo(request, pk):
    hilo = get_object_or_404(Hilo, pk=pk)
    if not puede_ver(request.user, hilo):
        raise PermissionDenied()
    if request.method == "POST":
        try:
            responder(request.user, hilo, request.POST.get("cuerpo"), request.FILES.get("archivo"))
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            return redirect("campus_hilo", pk=hilo.pk)
    marcar_hilo_leido(request.user, hilo)
    return render(request, "campus/hilo.html", _ctx(request, "mensajes", {"hilo": hilo}))


@login_required
@requiere_feature("campus.notificaciones")
def notificaciones(request):
    alumno = alumno_para_usuario(request.user)
    sync_notif(request.user, alumno)
    return render(
        request,
        "campus/notificaciones.html",
        _ctx(request, "mas", {"items": lista_notif(request.user)}),
    )


@login_required
@requiere_feature("campus.notificaciones")
@require_POST
def notificacion_leer(request, pk):
    marcar_una(request.user, pk)
    return redirect("campus_notificaciones")


@login_required
@requiere_feature("campus.notificaciones")
@require_POST
def notificaciones_leer_todas(request):
    marcar_todas(request.user)
    return redirect("campus_notificaciones")


@login_required
@requiere_feature("campus.ludico")
def ludico(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    perfil = perfil_de(alumno)
    if request.method == "POST":
        perfil.ranking_publico = bool(request.POST.get("ranking_publico"))
        perfil.save(update_fields=["ranking_publico"])
        messages.success(request, "Preferencia de ranking guardada.")
        return redirect("campus_ludico")
    return render(
        request,
        "campus/ludico.html",
        _ctx(
            request,
            "inicio",
            {
                "perfil": perfil,
                "insignias": perfil.insignias.select_related("insignia"),
                "ranking": ranking_ludico(),
            },
        ),
    )


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


@login_required
@requiere_feature("campus.credencial")
def credencial(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    return render(
        request,
        "campus/credencial.html",
        _ctx(request, "control", {"ficha": ficha_credencial(alumno)}),
    )


@login_required
@requiere_feature("campus.aceptacion")
def aceptacion(request):
    from campus.services.cursos import periodo_vigente

    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    periodo = periodo_vigente()
    abierta = ventana_abierta(periodo)
    if request.method == "POST":
        if not abierta:
            messages.error(request, "La ventana de aceptación no está abierta.")
            return redirect("campus_aceptacion")
        ins = get_object_or_404(
            Inscripcion, pk=request.POST.get("inscripcion_id"), alumno=alumno, periodo=periodo, estado="activo"
        )
        decision = request.POST.get("decision")
        if decision not in (AceptacionCarga.ESTADO_ACEPTADA, AceptacionCarga.ESTADO_CAMBIO):
            messages.error(request, "Indica si aceptas o solicitas un cambio.")
        elif hasattr(ins, "aceptacion"):
            messages.error(request, "Ya registraste un acuse para esa materia.")
        else:
            puede = ins.puede_cursar
            AceptacionCarga.objects.create(
                inscripcion=ins,
                estado=decision,
                comentario=(request.POST.get("comentario") or "").strip(),
            )
            ins.refresh_from_db()
            if ins.puede_cursar != puede:
                ins.puede_cursar = puede
                ins.save(update_fields=["puede_cursar"])
            messages.success(request, "Acuse guardado. El folio de Ventas no se modifica.")
            return redirect("campus_aceptacion")
    return render(
        request,
        "campus/aceptacion.html",
        _ctx(
            request,
            "control",
            {
                "periodo": periodo,
                "ventana": abierta,
                "inscripciones": carga_del_periodo(alumno, periodo),
            },
        ),
    )


@login_required
@requiere_feature("campus.normativa")
def normativa(request):
    docs = DocumentoNormativa.objects.filter(publicado=True)
    return render(request, "campus/normativa.html", _ctx(request, "control", {"documentos": docs}))


@login_required
@requiere_feature("campus.normativa")
def normativa_archivo(request, pk):
    doc = get_object_or_404(DocumentoNormativa, pk=pk, publicado=True)
    if not doc.archivo:
        raise Http404()
    return FileResponse(doc.archivo.open("rb"), as_attachment=True, filename=doc.archivo.name.split("/")[-1])


@login_required
@requiere_feature("campus.directorio")
def directorio(request):
    contactos = ContactoDirectorio.objects.filter(publicado=True)
    return render(request, "campus/directorio.html", _ctx(request, "control", {"contactos": contactos}))


@login_required
@requiere_feature("campus.ayuda")
def ayuda(request):
    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    if request.method == "POST":
        asunto = (request.POST.get("asunto") or "").strip()
        descripcion = (request.POST.get("descripcion") or "").strip()
        categoria = request.POST.get("categoria")
        adjunto = request.FILES.get("adjunto")
        if adjunto:
            try:
                validar_archivo(adjunto)
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
                adjunto = None
                asunto = ""
        if asunto and descripcion and categoria in dict(TicketAyuda.CATEGORIA_CHOICES):
            ticket = TicketAyuda.objects.create(
                alumno=alumno,
                categoria=categoria,
                asunto=asunto,
                descripcion=descripcion,
                adjunto=adjunto,
            )
            messages.success(request, f"Ticket {ticket.folio} abierto.")
            return redirect("campus_ayuda_detalle", pk=ticket.pk)
        if asunto or descripcion:
            messages.error(request, "Completa categoría, asunto y descripción.")
    tickets = TicketAyuda.objects.filter(alumno=alumno)
    return render(
        request,
        "campus/ayuda.html",
        _ctx(request, "control", {"tickets": tickets, "categorias": TicketAyuda.CATEGORIA_CHOICES}),
    )


@login_required
@requiere_feature("campus.ayuda")
def ayuda_detalle(request, pk):
    alumno = alumno_para_usuario(request.user)
    ticket = get_object_or_404(TicketAyuda, pk=pk, alumno=alumno)
    if request.method == "POST" and ticket.estado != TicketAyuda.ESTADO_CERRADO:
        cuerpo = (request.POST.get("cuerpo") or "").strip()
        if cuerpo:
            TicketRespuesta.objects.create(ticket=ticket, autor_id=request.user.pk, cuerpo=cuerpo, es_staff=False)
            return redirect("campus_ayuda_detalle", pk=ticket.pk)
    return render(request, "campus/ayuda_detalle.html", _ctx(request, "control", {"ticket": ticket}))


@login_required
@requiere_feature("campus.facturacion")
def facturacion(request):
    from django.utils import timezone as tz

    alumno = alumno_para_usuario(request.user)
    if alumno is None:
        messages.error(request, "No hay un expediente de alumno ligado a tu cuenta.")
        return redirect("campus_inicio")
    cliente = cliente_de_alumno(alumno)
    form = DatosFiscalesForm(request.POST or None, instance=cliente)
    if request.method == "POST" and form.is_valid():
        cliente = form.save(commit=False)
        cliente.factura_solicitada_en = tz.now()
        cliente.save()
        messages.success(request, "Datos fiscales guardados. Aún no hay CFDI para descargar.")
        return redirect("campus_facturacion")
    return render(
        request,
        "campus/facturacion.html",
        _ctx(request, "control", {"form": form, "cliente": cliente}),
    )
