from django.http import HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import redirect

from sii.identity import puede_ver_modulo


class ModuloAccessMiddleware:
    """Bloquea /ventas, /sii y /aula si el usuario no tiene el rol de esa superficie."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        path = request.path or "/"
        if path.startswith("/api"):
            from sii.identity import es_administrador

            if user is None or not user.is_authenticated or not es_administrador(user):
                return HttpResponseForbidden("API restringida.")
            return self.get_response(request)
        if user is not None and user.is_authenticated:
            modulo = None
            if path.startswith("/ventas"):
                modulo = "ventas"
            elif path.startswith("/sii") or path.startswith("/dashboard"):
                modulo = "sii"
            elif path.startswith("/aula"):
                modulo = "aula"
            if modulo and not puede_ver_modulo(user, modulo):
                messages.error(request, "No tienes acceso a ese módulo.")
                return redirect("inicio")
        return self.get_response(request)
