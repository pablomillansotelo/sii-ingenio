from django.contrib import admin

from .models import Actividad, CalificacionActividad, Kardex

admin.site.register(Actividad)
admin.site.register(CalificacionActividad)
admin.site.register(Kardex)
