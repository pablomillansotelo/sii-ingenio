from django.contrib import admin

from campus.models import AvisoInstitucional, AvisoLectura, CampusFavorito, Noticia


@admin.register(AvisoInstitucional)
class AvisoInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "publicado", "vigencia_inicio", "vigencia_fin")
    list_filter = ("tipo", "publicado")


admin.site.register(AvisoLectura)
admin.site.register(CampusFavorito)


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "publicada", "vigencia_inicio", "vigencia_fin", "creada_en")
    list_filter = ("publicada",)
