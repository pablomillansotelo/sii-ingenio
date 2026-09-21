"""Señales para mantener alineados ventas y SII."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Cliente, Producto
from .services import asegurar_curso_para_producto, sincronizar_alumno_desde_cliente

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Cliente)
def sincronizar_cliente_con_alumno(sender, instance, created, **kwargs):
    update_fields = kwargs.get("update_fields")
    if update_fields is not None and set(update_fields) <= {"id_alumno_sii"}:
        return
    sincronizar_alumno_desde_cliente(instance)


@receiver(post_save, sender=Producto)
def sincronizar_producto_con_curso(sender, instance, **kwargs):
    update_fields = kwargs.get("update_fields")
    if update_fields is not None and set(update_fields) <= {"id_curso"}:
        return
    asegurar_curso_para_producto(instance)
