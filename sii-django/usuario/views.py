from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from sii.identity import alumno_para_usuario, docente_para_usuario
from usuario.forms import PasswordChangeForm, PerfilForm
from ventas.models import Vendedor


def _telefono_de(user):
    alumno = alumno_para_usuario(user)
    if alumno and alumno.telefono:
        return alumno.telefono
    docente = docente_para_usuario(user)
    if docente and docente.telefono:
        return docente.telefono
    vendedor = Vendedor.para_usuario(user)
    if vendedor and vendedor.telefono:
        return vendedor.telefono
    return ""


def _guardar_perfil(user, nombre, apellido, telefono):
    user.first_name = nombre
    user.last_name = apellido
    user.save(update_fields=["first_name", "last_name"])
    alumno = alumno_para_usuario(user)
    if alumno:
        alumno.nombre = nombre or alumno.nombre
        alumno.apellido = apellido or alumno.apellido
        alumno.telefono = telefono
        alumno.save(update_fields=["nombre", "apellido", "telefono"])
    docente = docente_para_usuario(user)
    if docente:
        docente.nombre = nombre or docente.nombre
        docente.apellido = apellido or docente.apellido
        docente.telefono = telefono
        docente.save(update_fields=["nombre", "apellido", "telefono"])
    vendedor = Vendedor.para_usuario(user)
    if vendedor:
        vendedor.nombre = (f"{nombre} {apellido}").strip() or vendedor.nombre
        vendedor.telefono = telefono
        vendedor.save(update_fields=["nombre", "telefono"])


@login_required
def usuario(request):
    from sii.rbac import has_feature

    alumno = alumno_para_usuario(request.user)
    docente = docente_para_usuario(request.user)
    first_name = request.user.first_name or (alumno.nombre if alumno else "") or (docente.nombre if docente else "")
    last_name = request.user.last_name or (alumno.apellido if alumno else "") or (docente.apellido if docente else "")
    perfil = PerfilForm(
        request.POST if request.method == "POST" and request.POST.get("accion") == "perfil" else None,
        initial={
            "first_name": first_name,
            "last_name": last_name,
            "telefono": _telefono_de(request.user),
        },
    )
    password_form = PasswordChangeForm(
        request.user,
        request.POST if request.method == "POST" and request.POST.get("accion") == "password" else None,
    )
    if request.method == "POST" and request.POST.get("accion") == "perfil":
        if perfil.is_valid():
            _guardar_perfil(
                request.user,
                perfil.cleaned_data["first_name"],
                perfil.cleaned_data.get("last_name") or "",
                perfil.cleaned_data.get("telefono") or "",
            )
            messages.success(request, "Perfil actualizado.")
            return redirect("usuario")
        messages.error(request, "Revisa el nombre y el teléfono.")
    if request.method == "POST" and request.POST.get("accion") == "password":
        if password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Contraseña actualizada.")
            return redirect("usuario")
        messages.error(request, "No se pudo cambiar la contraseña.")
    return render(
        request,
        "usuario/usuario.html",
        {
            "perfil_form": perfil,
            "password_form": password_form,
            "ver_kardex": has_feature(request.user, "sii.kardex"),
        },
    )
