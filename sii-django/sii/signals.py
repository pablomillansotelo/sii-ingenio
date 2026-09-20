from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Alumno


@receiver(post_save, sender=Alumno)
def crear_usuario_para_alumno(sender, instance, created, **kwargs):
    if not created or instance.user_id is not None:
        return

    username = (
        f"{instance.nombre.lower().replace(' ', '_')}."
        f"{instance.apellido.lower().replace(' ', '_')}"
    )
    user = User.objects.filter(username=username).first()
    if user is None and instance.email:
        user = User.objects.filter(email=instance.email).first()
    if user is None:
        password = User.objects.make_random_password()
        user = User.objects.create_user(
            username=username,
            email=instance.email,
            password=password,
            first_name=instance.nombre,
            last_name=instance.apellido,
        )

    instance.user_id = user.id
    instance.save(update_fields=["user_id"])
