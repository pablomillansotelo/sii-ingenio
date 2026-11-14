from django.urls import reverse


def iniciales_de(nombre):
    partes = [p for p in (nombre or "").split() if p]
    letras = "".join(p[0] for p in partes)[:2].upper()
    return letras or "?"


def identidad_campus(user, alumno):
    if alumno:
        nombre = f"{alumno.nombre} {alumno.apellido}".strip()
        identificador = alumno.codigo_ingenio or f"Alumno #{alumno.pk}"
        etiqueta = "Código Ingenio" if alumno.codigo_ingenio else "Folio de alumno"
    else:
        nombre = (user.get_full_name() or user.get_username()).strip()
        identificador = user.get_username()
        etiqueta = "Usuario"
    correos = []
    if alumno and alumno.email:
        correos.append({"label": "Correo del expediente", "valor": alumno.email})
    cuenta_email = (getattr(user, "email", None) or "").strip()
    alumno_email = (alumno.email if alumno else "") or ""
    if cuenta_email and cuenta_email.lower() != alumno_email.lower():
        correos.append({"label": "Correo de la cuenta", "valor": cuenta_email})
    return {
        "nombre": nombre,
        "iniciales": iniciales_de(nombre),
        "identificador": identificador,
        "identificador_etiqueta": etiqueta,
        "correos": correos,
        "ficha_url": reverse("campus_ficha"),
        "cuenta_url": reverse("usuario"),
    }
