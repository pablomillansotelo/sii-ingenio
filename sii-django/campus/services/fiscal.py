from ventas.models import Cliente


REGIMENES = [
    ("601", "601 General de ley personas morales"),
    ("605", "605 Sueldos y salarios"),
    ("612", "612 Personas físicas con actividades empresariales"),
    ("616", "616 Sin obligaciones fiscales"),
    ("626", "626 Régimen simplificado de confianza"),
]


def cliente_de_alumno(alumno):
    if alumno is None:
        return None
    cliente = Cliente.objects.filter(id_alumno_sii=alumno).first()
    if cliente:
        return cliente
    cliente = Cliente.objects.filter(email__iexact=alumno.email).first()
    if cliente:
        if cliente.id_alumno_sii_id != alumno.pk:
            cliente.id_alumno_sii = alumno
            cliente.save(update_fields=["id_alumno_sii"])
        return cliente
    return Cliente.objects.create(
        nombre=(alumno.nombre or "")[:30],
        apellidos=(alumno.apellido or "")[:50],
        direccion="Por registrar",
        email=alumno.email,
        id_alumno_sii=alumno,
    )
