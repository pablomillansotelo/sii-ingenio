"""
Sistema de permisos y roles para la plataforma Ingenio.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group


# Nombres de grupos de usuarios
GRUPO_VENDEDOR = 'Vendedores'
GRUPO_DOCENTE = 'Docentes'
GRUPO_ALUMNO = 'Alumnos'
GRUPO_ADMINISTRADOR = 'Administradores'


def usuario_es_grupo(user, grupo_nombre):
    """
    Verifica si un usuario pertenece a un grupo específico.
    
    Args:
        user: Usuario de Django
        grupo_nombre: Nombre del grupo
        
    Returns:
        bool: True si el usuario pertenece al grupo
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True  # Los superusuarios tienen acceso a todo
    
    return user.groups.filter(name=grupo_nombre).exists()


def requiere_grupo(grupo_nombre):
    """
    Decorador para vistas que requieren pertenecer a un grupo específico.
    
    Usage:
        @requiere_grupo(GRUPO_DOCENTE)
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not usuario_es_grupo(request.user, grupo_nombre):
                raise PermissionDenied(f"Se requiere pertenecer al grupo: {grupo_nombre}")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def crear_grupos():
    """
    Crea los grupos de usuarios por defecto si no existen.
    Debe ejecutarse en una migración o comando de gestión.
    """
    grupos = [
        GRUPO_VENDEDOR,
        GRUPO_DOCENTE,
        GRUPO_ALUMNO,
        GRUPO_ADMINISTRADOR,
    ]
    
    for grupo_nombre in grupos:
        Group.objects.get_or_create(name=grupo_nombre)
    
    return grupos

