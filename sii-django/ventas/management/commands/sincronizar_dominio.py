from django.core.management.base import BaseCommand

from ventas.models import Producto, Venta
from ventas.services import asegurar_curso_para_producto, inscribir_desde_venta


class Command(BaseCommand):
    help = "Crea cursos SII para cada producto y genera inscripciones de ventas ya confirmadas."

    def handle(self, *args, **options):
        cursos = 0
        for producto in Producto.objects.all():
            asegurar_curso_para_producto(producto)
            cursos += 1
        inscripciones = 0
        for venta in Venta.objects.filter(estado="confirmada").select_related("id_cliente"):
            inscripciones += inscribir_desde_venta(venta)
        self.stdout.write(
            self.style.SUCCESS(
                f"Productos alineados: {cursos}. Inscripciones nuevas: {inscripciones}."
            )
        )
