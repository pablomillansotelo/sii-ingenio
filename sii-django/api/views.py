from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from sii.identity import alumnos_visibles, destino_post_login, inscripciones_visibles, puede_ver_modulo
from ventas.models import Cliente, Producto, Venta


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


@login_required
def inicio(request):
    stats = []
    if puede_ver_modulo(request.user, "ventas"):
        stats.extend(
            [
                {"label": "Clientes", "value": Cliente.objects.count(), "href": "Clientes"},
                {"label": "Ventas", "value": Venta.objects.count(), "href": "Ventas"},
                {"label": "Cursos", "value": Producto.objects.count(), "href": "Inventario"},
            ]
        )
    if puede_ver_modulo(request.user, "sii"):
        stats.extend(
            [
                {"label": "Alumnos", "value": alumnos_visibles(request.user).count(), "href": "sii_alumnos"},
                {"label": "Inscripciones", "value": inscripciones_visibles(request.user).count(), "href": "sii_inscripciones"},
            ]
        )
    ventas_recientes = []
    if puede_ver_modulo(request.user, "ventas"):
        ventas_recientes = Venta.objects.select_related("id_cliente").order_by("-id_venta")[:5]
    return render(
        request,
        "inicio.html",
        {"stats": stats, "ventas_recientes": ventas_recientes},
    )
