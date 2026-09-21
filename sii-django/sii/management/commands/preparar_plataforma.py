from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Grupos/roles + alineación Producto↔Curso e inscripciones de ventas."

    def handle(self, *args, **options):
        call_command("crear_grupos")
        call_command("sincronizar_dominio")
