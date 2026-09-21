"""
Sistema de permisos y roles para la plataforma Ingenio.
"""
from functools import wraps

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

GRUPO_VENDEDOR = "Vendedores"
GRUPO_DOCENTE = "Docentes"
GRUPO_ALUMNO = "Alumnos"
GRUPO_ADMINISTRADOR = "Administradores"


def usuario_es_grupo(user, grupo_nombre):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=grupo_nombre).exists()


def requiere_grupo(grupo_nombre):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not usuario_es_grupo(request.user, grupo_nombre):
                raise PermissionDenied(f"Se requiere pertenecer al grupo: {grupo_nombre}")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


class EsAdministradorAPI(BasePermission):
    """REST interno: solo superusuario o grupo Administradores."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return False
        from sii.identity import es_administrador

        return es_administrador(user)


def crear_grupos():
    nombres = [GRUPO_VENDEDOR, GRUPO_DOCENTE, GRUPO_ALUMNO, GRUPO_ADMINISTRADOR]
    for grupo_nombre in nombres:
        Group.objects.using("auth").get_or_create(name=grupo_nombre)
    return nombres
