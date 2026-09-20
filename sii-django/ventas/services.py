"""Sincronización de dominio: Cliente↔Alumno, Producto↔Curso, Venta→Inscripción."""
import logging
from datetime import date

from django.db import transaction

from sii.models import Alumno, Curso, Inscripcion, Periodo

logger = logging.getLogger(__name__)


def buscar_alumno_por_email(email):
    if not email:
        return None
    return Alumno.objects.filter(email=email).first()


def _curp_para_cliente(cliente):
    curp = (cliente.curp or "").strip().upper()
    if len(curp) == 18:
        return curp
    return f"TMP{cliente.id_cliente:015d}"[:18]


def crear_alumno_desde_cliente(cliente):
    existente = buscar_alumno_por_email(cliente.email)
    if existente:
        if cliente.id_alumno_sii_id != existente.pk:
            cliente.id_alumno_sii = existente
            cliente.save(update_fields=["id_alumno_sii"])
        return existente

    alumno = Alumno.objects.create(
        nombre=cliente.nombre,
        apellido=cliente.apellidos,
        email=cliente.email,
        curp=_curp_para_cliente(cliente),
        fecha_nacimiento=date(2000, 1, 1),
        estado="activo" if cliente.activo else "inactivo",
    )
    cliente.id_alumno_sii = alumno
    cliente.save(update_fields=["id_alumno_sii"])
    logger.info("Alumno %s creado desde cliente %s", alumno.pk, cliente.id_cliente)
    return alumno


def periodo_vigente(fecha=None):
    fecha = fecha or date.today()
    nombre = f"{fecha.year}"
    periodo = Periodo.objects.filter(nombre=nombre).first()
    if periodo:
        return periodo
    return Periodo.objects.create(
        nombre=nombre,
        fecha_inicio=date(fecha.year, 1, 1),
        fecha_fin=date(fecha.year, 12, 31),
    )


def asegurar_curso_para_producto(producto):
    nombre = (producto.producto or "Curso")[:100]
    descripcion = producto.descripcion or ""
    curso = producto.id_curso
    if curso is None:
        curso = Curso.objects.create(nombre=nombre, descripcion=descripcion or None)
        type(producto).objects.filter(pk=producto.pk).update(id_curso=curso)
        producto.id_curso = curso
        return curso
    campos = []
    if curso.nombre != nombre:
        curso.nombre = nombre
        campos.append("nombre")
    if (curso.descripcion or "") != descripcion:
        curso.descripcion = descripcion or None
        campos.append("descripcion")
    if campos:
        curso.save(update_fields=campos)
    return curso


def inscribir_desde_venta(venta):
    cliente = venta.id_cliente
    alumno = cliente.id_alumno_sii or crear_alumno_desde_cliente(cliente)
    periodo = periodo_vigente(venta.fecha)
    creadas = 0
    for detalle in venta.ventadetalle_set.select_related("id_producto"):
        producto = detalle.id_producto
        curso = asegurar_curso_para_producto(producto)
        _, created = Inscripcion.objects.get_or_create(
            alumno=alumno,
            curso=curso,
            defaults={"periodo": periodo, "estado": "activo"},
        )
        if created:
            creadas += 1
    return creadas
