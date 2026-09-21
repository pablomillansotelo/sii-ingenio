from django.core.management.base import BaseCommand

from sii.identity import asignar_grupos_desde_dominio
from sii.permissions import crear_grupos


class Command(BaseCommand):
    help = "Crea grupos de rol y los asigna según vendedor, docente y alumno."

    def handle(self, *args, **options):
        grupos = crear_grupos()
        self.stdout.write(self.style.SUCCESS(f"Grupos: {', '.join(grupos)}"))
        asignados = asignar_grupos_desde_dominio()
        for nombre, cantidad in asignados.items():
            self.stdout.write(f"  {nombre}: {cantidad}")
