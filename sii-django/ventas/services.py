"""Sincronización de dominio: Cliente↔Alumno, Producto↔Curso, Venta→Inscripción."""
import logging
from datetime import date
from typing import NamedTuple

from django.db import transaction

from sii.models import Alumno, Curso, Inscripcion, Periodo

logger = logging.getLogger(__name__)


class ResultadoInscripcion(NamedTuple):
    creadas: int = 0
    reactivadas: int = 0
    ya_inscritas: int = 0

    def __int__(self):
        return self.creadas


def buscar_alumno_por_email(email):
    if not email:
        return None
    return Alumno.objects.filter(email__iexact=email).first()


def _curp_para_cliente(cliente):
    curp = (cliente.curp or "").strip().upper()
    if len(curp) == 18:
        return curp
    return f"TMP{cliente.id_cliente:015d}"[:18]


def _vincular_cliente_alumno(cliente, alumno):
    if cliente.id_alumno_sii_id != alumno.pk:
        cliente.id_alumno_sii = alumno
        cliente.save(update_fields=["id_alumno_sii"])


def sincronizar_alumno_desde_cliente(cliente):
    """Crea o actualiza el Alumno ligado al cliente (alta y edición)."""
    alumno = cliente.id_alumno_sii
    if alumno is None:
        alumno = buscar_alumno_por_email(cliente.email)
    if alumno is None:
        alumno = Alumno.objects.create(
            nombre=cliente.nombre,
            apellido=cliente.apellidos,
            email=cliente.email,
            curp=_curp_para_cliente(cliente),
            fecha_nacimiento=date(2000, 1, 1),
            estado="activo" if cliente.activo else "inactivo",
        )
        _vincular_cliente_alumno(cliente, alumno)
        logger.info("Alumno %s creado desde cliente %s", alumno.pk, cliente.id_cliente)
        return alumno

    campos = []
    if alumno.nombre != cliente.nombre:
        alumno.nombre = cliente.nombre
        campos.append("nombre")
    if alumno.apellido != (cliente.apellidos or ""):
        alumno.apellido = cliente.apellidos or ""
        campos.append("apellido")
    if (alumno.email or "").lower() != (cliente.email or "").lower():
        if cliente.email and not Alumno.objects.filter(email__iexact=cliente.email).exclude(pk=alumno.pk).exists():
            alumno.email = cliente.email
            campos.append("email")
    curp = (cliente.curp or "").strip().upper()
    if len(curp) == 18 and alumno.curp != curp:
        if not Alumno.objects.filter(curp=curp).exclude(pk=alumno.pk).exists():
            alumno.curp = curp
            campos.append("curp")
    estado = "activo" if cliente.activo else "inactivo"
    if alumno.estado in ("activo", "inactivo") and alumno.estado != estado:
        alumno.estado = estado
        campos.append("estado")
    if campos:
        alumno.save(update_fields=campos)
    _vincular_cliente_alumno(cliente, alumno)
    return alumno


def crear_alumno_desde_cliente(cliente):
    return sincronizar_alumno_desde_cliente(cliente)


def periodo_vigente(fecha=None):
    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha[:10])
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


def _puede_cursar_desde_venta(venta):
    return (venta.estado_pago or "") == "pagado"


def inscribir_desde_venta(venta):
    """Un folio = un alumno. `cantidad>1` reserva cupo, no clona inscripciones."""
    cliente = venta.id_cliente
    alumno = sincronizar_alumno_desde_cliente(cliente)
    periodo = periodo_vigente(venta.fecha)
    creadas = reactivadas = ya = 0
    puede = _puede_cursar_desde_venta(venta)
    for detalle in venta.ventadetalle_set.select_related("id_producto", "id_edicion"):
        producto = detalle.id_producto
        curso = asegurar_curso_para_producto(producto)
        edicion = detalle.id_edicion
        existente = Inscripcion.objects.filter(
            alumno=alumno, curso=curso, periodo=periodo
        ).first()
        if existente:
            if existente.estado == "cancelado":
                existente.reintentar(periodo=periodo, reservar=False)
                existente.id_edicion = edicion
                existente.puede_cursar = puede
                existente.save(update_fields=["id_edicion", "puede_cursar"])
                reactivadas += 1
            else:
                campos = []
                if edicion is not None and existente.id_edicion_id != edicion.pk:
                    existente.id_edicion = edicion
                    campos.append("id_edicion")
                if existente.puede_cursar != puede:
                    existente.puede_cursar = puede
                    campos.append("puede_cursar")
                if campos:
                    existente.save(update_fields=campos)
                ya += 1
            continue
        Inscripcion.objects.create(
            alumno=alumno,
            curso=curso,
            periodo=periodo,
            id_edicion=edicion,
            estado="activo",
            puede_cursar=puede,
        )
        creadas += 1
    return ResultadoInscripcion(creadas=creadas, reactivadas=reactivadas, ya_inscritas=ya)


def sincronizar_puede_cursar(venta):
    alumno = venta.id_cliente.id_alumno_sii if venta.id_cliente_id else None
    if alumno is None:
        return 0
    puede = _puede_cursar_desde_venta(venta)
    actualizadas = 0
    for detalle in venta.ventadetalle_set.select_related("id_producto", "id_edicion"):
        curso = detalle.id_producto.id_curso
        if curso is None:
            continue
        qs = Inscripcion.objects.filter(alumno=alumno, curso=curso).exclude(estado="cancelado")
        if detalle.id_edicion_id:
            qs = qs.filter(id_edicion_id=detalle.id_edicion_id)
        actualizadas += qs.update(puede_cursar=puede)
    return actualizadas


def peek_inscripciones_cliente(cliente):
    alumno = cliente.id_alumno_sii or buscar_alumno_por_email(cliente.email)
    if alumno is None:
        return []
    filas = (
        Inscripcion.objects.filter(alumno=alumno, estado="activo")
        .select_related("curso", "periodo", "id_edicion")
        .order_by("curso__nombre")
    )
    resultado = []
    for inscripcion in filas:
        edicion = inscripcion.id_edicion
        resultado.append(
            {
                "curso": inscripcion.curso.nombre,
                "periodo": inscripcion.periodo.nombre if inscripcion.periodo_id else "",
                "edicion": edicion.codigo_edicion if edicion else "",
                "puede_cursar": inscripcion.puede_cursar,
            }
        )
    return resultado


@transaction.atomic
def baja_inscripciones_de_venta(venta, liberar=False):
    alumno = venta.id_cliente.id_alumno_sii if venta.id_cliente_id else None
    if alumno is None:
        return 0
    bajas = 0
    for detalle in venta.ventadetalle_set.select_related("id_producto", "id_edicion"):
        curso = detalle.id_producto.id_curso
        if curso is None:
            continue
        qs = Inscripcion.objects.filter(alumno=alumno, curso=curso).exclude(estado="cancelado")
        if detalle.id_edicion_id:
            qs = qs.filter(id_edicion_id=detalle.id_edicion_id)
        for inscripcion in qs:
            inscripcion.dar_baja(liberar=liberar)
            bajas += 1
    return bajas
