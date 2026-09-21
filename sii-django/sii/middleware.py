from django.http import HttpResponseForbidden

from sii.rbac import feature_para_url, has_any_feature


class FeatureAccessMiddleware:
    """Candado por feature de la URL (process_view: resolver_match ya existe)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        path = request.path or "/"
        if path.startswith("/api"):
            from sii.identity import es_administrador

            if user is None or not user.is_authenticated or not es_administrador(user):
                return HttpResponseForbidden("API restringida.")
            return None
        if user is None or not user.is_authenticated:
            return None
        match = getattr(request, "resolver_match", None)
        url_name = getattr(match, "url_name", None) if match else None
        requerida = feature_para_url(url_name)
        if requerida is None:
            return None
        if not has_any_feature(user, requerida):
            return HttpResponseForbidden("No tienes acceso a esa función.")
        return None


# Alias: el nombre viejo aparece en docs y deploys previos.
ModuloAccessMiddleware = FeatureAccessMiddleware
