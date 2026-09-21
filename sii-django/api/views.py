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
    stats_ventas = []
    stats_sii = []
    ventas_recientes = []
    if puede_ver_modulo(request.user, "ventas"):
        pagos_pendientes = Venta.objects.filter(estado_pago="pendiente").count()
        stats_ventas = [
            {"label": "Clientes", "value": Cliente.objects.filter(activo=True).count(), "href": "Clientes"},
            {"label": "Folios", "value": Venta.objects.count(), "href": "Ventas"},
            {"label": "Cursos en venta", "value": Producto.objects.filter(activo=True).count(), "href": "Inventario"},
            {"label": "Pagos pendientes", "value": pagos_pendientes, "href": "Pagos"},
        ]
        ventas_recientes = (
            Venta.objects.select_related("id_cliente")
            .prefetch_related("ventadetalle_set")
            .order_by("-id_venta")[:8]
        )
    if puede_ver_modulo(request.user, "sii"):
        stats_sii = [
            {"label": "Alumnos", "value": alumnos_visibles(request.user).count(), "href": "sii_alumnos"},
            {
                "label": "Inscripciones",
                "value": inscripciones_visibles(request.user).count(),
                "href": "sii_inscripciones",
            },
        ]
    return render(
        request,
        "inicio.html",
        {
            "stats_ventas": stats_ventas,
            "stats_sii": stats_sii,
            "ventas_recientes": ventas_recientes,
        },
    )
