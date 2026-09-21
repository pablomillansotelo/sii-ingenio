"""Identidad, roles inferidos y querysets por alcance."""
from django.contrib.auth import get_user_model
from django.db.models import Q

from docente.models import Docente
from sii.models import Alumno
from sii.permissions import (
    GRUPO_ADMINISTRADOR,
    GRUPO_ALUMNO,
    GRUPO_DOCENTE,
    GRUPO_VENDEDOR,
    usuario_es_grupo,
)
from ventas.models import Vendedor

MODULOS = ("ventas", "sii", "aula")


def alumno_para_usuario(user):
    if user is None or not user.is_authenticated:
        return None
    alumno = Alumno.objects.filter(user_id=user.pk).first()
    if alumno:
        return alumno
    email = (getattr(user, "email", None) or "").strip()
    if not email:
        return None
    alumno = Alumno.objects.filter(email__iexact=email).first()
    if alumno and alumno.user_id != user.pk:
        alumno.user_id = user.pk
        alumno.save(update_fields=["user_id"])
    return alumno


def docente_para_usuario(user):
    if user is None or not user.is_authenticated:
        return None
    docente = Docente.objects.filter(user_id=user.pk).first()
    if docente:
        return docente
    email = (getattr(user, "email", None) or "").strip()
    if not email:
        return None
    docente = Docente.objects.filter(email__iexact=email).first()
    if docente and docente.user_id != user.pk:
        docente.user_id = user.pk
        docente.save(update_fields=["user_id"])
    return docente


def es_administrador(user):
    return usuario_es_grupo(user, GRUPO_ADMINISTRADOR)


def _nombres_grupos(user):
    return set(user.groups.values_list("name", flat=True))


def _roles_desde_grupos(user):
    return _nombres_grupos(user) & {
        GRUPO_VENDEDOR,
        GRUPO_DOCENTE,
        GRUPO_ALUMNO,
        GRUPO_ADMINISTRADOR,
    }


def roles_inferidos(user):
    """Unión de grupos explícitos y fichas de dominio (vendedor + docente, etc.)."""
    if user is None or not getattr(user, "is_authenticated", False):
        return set()
    cached = getattr(user, "_ingenio_roles", None)
    if cached is not None:
        return cached
    if user.is_superuser:
        roles = {GRUPO_ADMINISTRADOR}
        user._ingenio_roles = roles
        return roles
    roles = set(_roles_desde_grupos(user))
    if Vendedor.objects.filter(user_id=user.pk, activo=True).exists():
        roles.add(GRUPO_VENDEDOR)
    if docente_para_usuario(user) is not None:
        roles.add(GRUPO_DOCENTE)
    if alumno_para_usuario(user) is not None:
        roles.add(GRUPO_ALUMNO)
    user._ingenio_roles = roles
    return roles


def modulos_permitidos(user):
    from sii.rbac import dominios_permitidos

    return dominios_permitidos(user)


def puede_ver_modulo(user, modulo):
    return modulo in modulos_permitidos(user)


def destino_post_login(user):
    permitidos = modulos_permitidos(user)
    if permitidos == {"aula"}:
        return "aula_dashboard"
    if permitidos == {"ventas"}:
        return "ventas_home"
    if permitidos == {"sii"}:
        return "sii_home"
    return "inicio"


def asignar_grupos_desde_dominio():
    from django.contrib.auth.models import Group

    User = get_user_model()
    grupos = {nombre: Group.objects.using("auth").get_or_create(name=nombre)[0] for nombre in (
        GRUPO_VENDEDOR, GRUPO_DOCENTE, GRUPO_ALUMNO, GRUPO_ADMINISTRADOR,
    )}
    asignados = {GRUPO_VENDEDOR: 0, GRUPO_DOCENTE: 0, GRUPO_ALUMNO: 0, GRUPO_ADMINISTRADOR: 0}
    rol_por_usuario = {}

    def marcar(user, rol):
        if user is None:
            return
        entrada = rol_por_usuario.get(user.pk)
        if entrada is None:
            rol_por_usuario[user.pk] = (user, {rol})
        else:
            entrada[1].add(rol)

    for user in User.objects.using("auth").filter(is_superuser=True):
        marcar(user, GRUPO_ADMINISTRADOR)

    for vendedor in Vendedor.objects.filter(activo=True):
        if not vendedor.user_id:
            continue
        user = User.objects.using("auth").filter(pk=vendedor.user_id).first()
        marcar(user, GRUPO_VENDEDOR)

    for docente in Docente.objects.all():
        user = None
        if docente.user_id:
            user = User.objects.using("auth").filter(pk=docente.user_id).first()
        if user is None and docente.email:
            user = User.objects.using("auth").filter(email__iexact=docente.email).first()
        if user is None:
            continue
        if docente.user_id != user.pk:
            docente.user_id = user.pk
            docente.save(update_fields=["user_id"])
        marcar(user, GRUPO_DOCENTE)

    for alumno in Alumno.objects.all():
        user = None
        if alumno.user_id:
            user = User.objects.using("auth").filter(pk=alumno.user_id).first()
        if user is None and alumno.email:
            user = User.objects.using("auth").filter(email__iexact=alumno.email).first()
        if user is None:
            continue
        if alumno.user_id != user.pk:
            alumno.user_id = user.pk
            alumno.save(update_fields=["user_id"])
        marcar(user, GRUPO_ALUMNO)

    nuestros = list(grupos.values())
    for user, roles in rol_por_usuario.values():
        user.groups.remove(*nuestros)
        user.groups.add(*(grupos[rol] for rol in roles))
        for rol in roles:
            asignados[rol] += 1

    return asignados


def alumnos_visibles(user):
    from sii.models import Alumno

    if es_administrador(user):
        return Alumno.objects.all()
    docente = docente_para_usuario(user)
    if docente is not None:
        from sii.models import Inscripcion

        alumno_ids = Inscripcion.objects.filter(
            curso_id__in=docente.cursos_asignados.values_list("curso_id", flat=True)
        ).values_list("alumno_id", flat=True)
        return Alumno.objects.filter(pk__in=alumno_ids)
    alumno = alumno_para_usuario(user)
    if alumno is not None:
        return Alumno.objects.filter(pk=alumno.pk)
    return Alumno.objects.none()


def cursos_visibles(user):
    from sii.models import Curso, Inscripcion

    qs = Curso.objects.select_related("oferta")
    if es_administrador(user):
        return qs
    curso_ids = set()
    docente = docente_para_usuario(user)
    if docente is not None:
        curso_ids.update(docente.cursos_asignados.values_list("curso_id", flat=True))
    alumno = alumno_para_usuario(user)
    if alumno is not None:
        curso_ids.update(Inscripcion.objects.filter(alumno=alumno).values_list("curso_id", flat=True))
    if not curso_ids:
        return qs.none()
    return qs.filter(pk__in=curso_ids)


def inscripciones_visibles(user):
    from sii.models import Inscripcion

    qs = Inscripcion.objects.select_related("alumno", "curso", "periodo")
    if es_administrador(user):
        return qs
    docente = docente_para_usuario(user)
    if docente is not None:
        return qs.filter(curso_id__in=docente.cursos_asignados.values_list("curso_id", flat=True))
    alumno = alumno_para_usuario(user)
    if alumno is not None:
        return qs.filter(alumno=alumno)
    return qs.none()


def ventas_visibles(user):
    from sii.rbac import has_feature, scope_for
    from ventas.models import Venta

    qs = Venta.objects.select_related("id_cliente", "id_vendedor")
    if has_feature(user, "ventas.folios") and scope_for(user, "ventas.folios") == "all":
        return qs
    if has_feature(user, "ventas.mis_compras"):
        alumno = alumno_para_usuario(user)
        if alumno is None:
            return qs.none()
        filtro = Q(id_cliente__id_alumno_sii=alumno)
        email = (alumno.email or "").strip()
        if email:
            filtro |= Q(id_cliente__email__iexact=email)
        return qs.filter(filtro)
    return qs.none()
