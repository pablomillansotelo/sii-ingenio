from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.shortcuts import redirect, render

from sii.models import Alumno, Inscripcion
from ventas.models import Cliente, Producto, Venta


class CustomLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)


@login_required
def inicio(request):
    return render(
        request,
        "inicio.html",
        {
            "stats": [
                {"label": "Clientes", "value": Cliente.objects.count(), "href": "Clientes"},
                {"label": "Ventas", "value": Venta.objects.count(), "href": "Ventas"},
                {"label": "Alumnos", "value": Alumno.objects.count(), "href": "sii_alumnos"},
                {"label": "Cursos", "value": Producto.objects.count(), "href": "Inventario"},
                {"label": "Inscripciones", "value": Inscripcion.objects.count(), "href": "sii_inscripciones"},
            ],
            "ventas_recientes": Venta.objects.select_related("id_cliente").order_by("-id_venta")[:5],
        },
    )
