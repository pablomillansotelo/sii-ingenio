# alumnos/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Alumno

@receiver(post_save, sender=Alumno)
def crear_usuario_para_alumno(sender, instance, created, **kwargs):
    if created and instance.user_id is None:
        # Puedes personalizar el username y password como desees
        username = f"{instance.nombre.lower().replace(' ', '_')}.{instance.apellido.lower().replace(' ', '_')}"
        first_name = instance.nombre
        last_name = instance.apellido
        email = instance.email
        password = User.objects.make_random_password()

        user = User.objects.create_user(username=username, email=email, password=password,
                                         first_name=first_name, last_name=last_name)

        # Asignamos el ID del usuario creado al alumno y lo guardamos otra vez
        instance.user_id = user.id
        instance.save()