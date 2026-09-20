"""
Comando de gestión para crear grupos de usuarios por defecto.
Ejecutar: python manage.py crear_grupos
"""
from django.core.management.base import BaseCommand
from sii.permissions import crear_grupos


class Command(BaseCommand):
    help = 'Crea los grupos de usuarios por defecto (Vendedores, Docentes, Alumnos, Administradores)'

    def handle(self, *args, **options):
        grupos = crear_grupos()
        self.stdout.write(
            self.style.SUCCESS(f'Grupos creados exitosamente: {", ".join(grupos)}')
        )




