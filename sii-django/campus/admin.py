from django.contrib import admin

from campus.models import AvisoInstitucional, AvisoLectura


@admin.register(AvisoInstitucional)
class AvisoInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "publicado", "vigencia_inicio", "vigencia_fin")
    list_filter = ("tipo", "publicado")


admin.site.register(AvisoLectura)
