"""XP motivacional. Nunca escribe kardex, actas ni saldo de Ventas.

Reglas: nivel = 1 + xp // 100. Por cada 10 XP se suma 1 moneda Ingenio (no es dinero).
"""
from django.utils import timezone

from campus.models import Insignia, InsigniaAlumno, MovimientoXP, PerfilLudico

XP_ENTREGA = 10
INSIGNIAS = (
    ("primeros_pasos", "Primeros pasos", "Llegaste al nivel 2."),
    ("constancia", "Constancia", "Llegaste al nivel 5."),
    ("trayecto", "Trayecto Ingenio", "Llegaste al nivel 10."),
)


def perfil_de(alumno):
    if alumno is None:
        return None
    perfil, _ = PerfilLudico.objects.get_or_create(alumno=alumno)
    return perfil


def nivel_de(xp):
    return 1 + int(xp or 0) // 100


def asegurar_catalogo():
    for clave, nombre, desc in INSIGNIAS:
        Insignia.objects.get_or_create(clave=clave, defaults={"nombre": nombre, "descripcion": desc})


def _otorgar_insignias(perfil):
    asegurar_catalogo()
    nivel = perfil.nivel
    umbrales = {2: "primeros_pasos", 5: "constancia", 10: "trayecto"}
    for min_nivel, clave in umbrales.items():
        if nivel >= min_nivel:
            ins = Insignia.objects.filter(clave=clave).first()
            if ins:
                InsigniaAlumno.objects.get_or_create(perfil=perfil, insignia=ins)


def acreditar(alumno, cantidad, motivo, clave, autor_id=None):
    if alumno is None or int(cantidad) == 0:
        return None
    perfil = perfil_de(alumno)
    if MovimientoXP.objects.filter(perfil=perfil, clave=clave).exists():
        return perfil
    cantidad = int(cantidad)
    MovimientoXP.objects.create(
        perfil=perfil, cantidad=cantidad, motivo=motivo[:160], clave=clave[:80], creado_por_id=autor_id
    )
    if cantidad > 0:
        perfil.xp = int(perfil.xp) + cantidad
        perfil.monedas = int(perfil.monedas) + cantidad // 10
    else:
        perfil.xp = max(0, int(perfil.xp) + cantidad)
    perfil.save(update_fields=["xp", "monedas", "actualizado_en"])
    _otorgar_insignias(perfil)
    return perfil


def resetear(alumno, autor_id):
    perfil = perfil_de(alumno)
    clave = f"reset-{timezone.now().isoformat()}"
    MovimientoXP.objects.create(
        perfil=perfil,
        cantidad=-int(perfil.xp),
        motivo="Reinicio de staff",
        clave=clave[:80],
        creado_por_id=autor_id,
    )
    perfil.xp = 0
    perfil.monedas = 0
    perfil.reset_en = timezone.now()
    perfil.reset_por_id = autor_id
    perfil.save()
    perfil.insignias.all().delete()
    return perfil


def ranking():
    return (
        PerfilLudico.objects.filter(ranking_publico=True)
        .select_related("alumno")
        .order_by("-xp", "alumno_id")[:20]
    )
