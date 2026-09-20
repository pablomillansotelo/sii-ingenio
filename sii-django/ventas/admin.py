from django.contrib import admin

from .models import Cliente, EdicionCurso, Pago, Producto, Vendedor, Venta, VentaDetalle

admin.site.register(Vendedor)
admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(EdicionCurso)
admin.site.register(Venta)
admin.site.register(VentaDetalle)
admin.site.register(Pago)
