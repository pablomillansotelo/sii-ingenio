from django.db.models.signals import post_save
from django.dispatch import receiver

from sii.accounts import provisionar_persona
from sii.models import Alumno, Docente


def _provisionar_si_alta(instance, created, kwargs):
    if not created:
        return
    update_fields = kwargs.get("update_fields")
    if update_fields is not None and set(update_fields) <= {"user_id"}:
        return
    provisionar_persona(instance, temporal=False)


@receiver(post_save, sender=Alumno)
def crear_usuario_para_alumno(sender, instance, created, **kwargs):
    _provisionar_si_alta(instance, created, kwargs)


@receiver(post_save, sender=Docente)
def crear_usuario_para_docente(sender, instance, created, **kwargs):
    _provisionar_si_alta(instance, created, kwargs)
