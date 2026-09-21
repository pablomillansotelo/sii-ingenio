"""Alta de cuenta de login para alumno, docente y vendedor."""
from __future__ import annotations

import re
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.text import slugify

from sii.permissions import GRUPO_ALUMNO, GRUPO_DOCENTE, GRUPO_VENDEDOR

User = get_user_model()


@dataclass
class CuentaProvisionada:
    user: object
    creada: bool
    password_temporal: str | None = None

    def mensaje(self) -> str:
        if self.password_temporal:
            return (
                f"Usuario {self.user.username}. Contraseña temporal: {self.password_temporal}. "
                "Cópiala ahora; no se vuelve a mostrar."
            )
        return f"Cuenta vinculada: {self.user.username}."


def _username_base(nombre, apellido, email):
    partes = [slugify(nombre or ""), slugify(apellido or "")]
    base = ".".join(p for p in partes if p)[:40]
    if not base:
        local = (email or "usuario").split("@")[0]
        base = slugify(local) or "usuario"
    base = re.sub(r"[^a-z0-9._]", "", base.lower()) or "usuario"
    return base[:40]


def _username_unico(base):
    username = base
    n = 1
    while User.objects.filter(username=username).exists():
        n += 1
        username = f"{base}{n}"[:150]
    return username


def _asignar_grupo(user, grupo_nombre):
    if not grupo_nombre:
        return
    grupo, _ = Group.objects.using("auth").get_or_create(name=grupo_nombre)
    user.groups.add(grupo)


def buscar_usuario(email=None, user_id=None):
    if user_id:
        user = User.objects.filter(pk=user_id).first()
        if user:
            return user
    email = (email or "").strip()
    if not email:
        return None
    return User.objects.filter(email__iexact=email).first()


def provisionar_usuario(
    *,
    email,
    nombre="",
    apellido="",
    grupo=None,
    user_id=None,
    temporal=False,
):
    """Crea o vincula un User y le suma el grupo (unión)."""
    user = buscar_usuario(email=email, user_id=user_id)
    creada = False
    password = None
    if user is None:
        username = _username_unico(_username_base(nombre, apellido, email))
        user = User(username=username, email=email or "", first_name=nombre or "", last_name=apellido or "")
        if temporal:
            password = User.objects.make_random_password(length=12)
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        creada = True
    else:
        campos = []
        if nombre and not user.first_name:
            user.first_name = nombre
            campos.append("first_name")
        if apellido and not user.last_name:
            user.last_name = apellido
            campos.append("last_name")
        if email and not user.email:
            user.email = email
            campos.append("email")
        if campos:
            user.save(update_fields=campos)
        if temporal and not user.has_usable_password():
            password = User.objects.make_random_password(length=12)
            user.set_password(password)
            user.save(update_fields=["password"])
    _asignar_grupo(user, grupo)
    if hasattr(user, "_ingenio_roles"):
        delattr(user, "_ingenio_roles")
    if hasattr(user, "_ingenio_features"):
        delattr(user, "_ingenio_features")
    return CuentaProvisionada(user=user, creada=creada, password_temporal=password)


def emitir_password_temporal(user):
    password = User.objects.make_random_password(length=12)
    user.set_password(password)
    user.save(update_fields=["password"])
    return password


def grupo_para_modelo(instance):
    from docente.models import Docente
    from sii.models import Alumno
    from ventas.models import Vendedor

    if isinstance(instance, Alumno):
        return GRUPO_ALUMNO
    if isinstance(instance, Docente):
        return GRUPO_DOCENTE
    if isinstance(instance, Vendedor):
        return GRUPO_VENDEDOR
    return None


def provisionar_persona(instance, temporal=False):
    """Asegura User + grupo y escribe user_id si faltaba."""
    grupo = grupo_para_modelo(instance)
    nombre = getattr(instance, "nombre", "") or ""
    apellido = getattr(instance, "apellido", "") or ""
    email = getattr(instance, "email", "") or ""
    cuenta = provisionar_usuario(
        email=email,
        nombre=nombre,
        apellido=apellido,
        grupo=grupo,
        user_id=getattr(instance, "user_id", None),
        temporal=temporal,
    )
    if instance.user_id != cuenta.user.pk:
        instance.user_id = cuenta.user.pk
        instance.save(update_fields=["user_id"])
    instance._cuenta = cuenta
    return cuenta
