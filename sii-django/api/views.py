from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from api.inicio import cargar_registro
from api.inicio.conteos import conteos_para
from api.inicio.contextos import CONTEXTOS, contexto_activo, contextos_disponibles
from api.inicio.badges import contar_contexto
from api.inicio.servir import cargar_widgets
from api.inicio.utils import reverse_home
from sii.identity import destino_post_login, es_persona_campus, modulos_permitidos
from sii.rbac import HOY_SHORTCUTS, has_feature, visible_en_menu


class CustomLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self._destino(request.user))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(destino_post_login(self.request.user))

    @staticmethod
    def _destino(user):
        return reverse(destino_post_login(user))


def _atajos_contexto(user, contexto):
    atajos = []
    for item in HOY_SHORTCUTS:
        if item.get("contexto") and item["contexto"] != contexto:
            continue
        if not visible_en_menu(user, item):
            continue
        atajos.append(item)
    return atajos


def _atajos_todo_al_dia(user, contexto):
    if contexto == "escolar":
        nombres = (
            ("sii_alumnos", "Alumnos", "bi-people"),
            ("sii_inscripciones", "Inscripciones", "bi-clipboard-check"),
            ("sii_periodos", "Periodos", "bi-calendar3"),
        )
        return [{"label": label, "url_name": name, "icon": icon} for name, label, icon in nombres]
    return _atajos_contexto(user, contexto)[:3]


@login_required
def inicio(request):
    user = request.user
    if es_persona_campus(user) and has_feature(user, "campus.inicio"):
        return redirect("campus_inicio")
    if es_persona_campus(user):
        if has_feature(user, "sii.kardex"):
            return redirect("sii_kardex")
        return render(
            request,
            "inicio/index.html",
            {
                "inicio_ctx": None,
                "inicio_ctx_label": "",
                "inicio_subtitle": "Tu mesa de trabajo en Ingenio.",
                "inicio_tabs": [],
                "widgets_pendientes": [],
                "widgets_vacios": [],
                "todo_al_dia": False,
                "sin_modulo": True,
                "conteos": [],
                "mostrar_mi_campus": False,
                "atajos_vacios": [],
            },
        )

    cargar_registro()
    user._inicio_request = request
    hoy = timezone.localdate()
    ctx = contexto_activo(request)
    disponibles = contextos_disponibles(user)
    cargados = cargar_widgets(user, ctx, hoy) if ctx else []
    tabs = []
    if len(disponibles) >= 2:
        activos = sum(int(data.count or 0) for _widget, data in cargados)
        for item in disponibles:
            badge = activos if item["clave"] == ctx else contar_contexto(user, item["clave"], hoy)
            tabs.append({**item, "badge": badge, "active": item["clave"] == ctx})
    pendientes = [(w, d) for w, d in cargados if d.tipo == "kpi" or d.count]
    vacios = [(w, d) for w, d in cargados if d.tipo != "kpi" and not d.count]
    sin_modulo = not modulos_permitidos(user) and not ctx
    todo_al_dia = bool(ctx) and not pendientes and not sin_modulo
    mostrar_mi_campus = (not es_persona_campus(user)) and has_feature(user, "campus.inicio")
    campus_url = reverse_home("campus_inicio", "mi-campus") if mostrar_mi_campus else ""
    meta = CONTEXTOS.get(ctx or "", {})
    label = meta.get("label", "")
    conteos = conteos_para(user, ctx) if ctx and ctx != "direccion" else []
    if label:
        subtitle = f"Lo que hay que hacer ahora en {label}."
    else:
        subtitle = "Tu mesa de trabajo en Ingenio."

    return render(
        request,
        "inicio/index.html",
        {
            "inicio_ctx": ctx,
            "inicio_ctx_label": label,
            "inicio_subtitle": subtitle,
            "inicio_tabs": tabs,
            "widgets_pendientes": pendientes,
            "widgets_vacios": vacios,
            "todo_al_dia": todo_al_dia,
            "sin_modulo": sin_modulo,
            "conteos": conteos,
            "mostrar_mi_campus": mostrar_mi_campus,
            "campus_url": campus_url,
            "atajos_vacios": _atajos_todo_al_dia(user, ctx) if todo_al_dia else [],
        },
    )
