from django.contrib import admin

from .models import Actividad, AvisoGrupo, CalificacionActividad, Kardex, Recurso, SeccionTema

admin.site.register(Actividad)
admin.site.register(CalificacionActividad)
admin.site.register(Kardex)
admin.site.register(SeccionTema)
admin.site.register(Recurso)
admin.site.register(AvisoGrupo)
