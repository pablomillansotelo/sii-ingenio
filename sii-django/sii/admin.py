from django.contrib import admin

from sii.models import (
    ActaFinal,
    ActaRenglon,
    Alumno,
    Curso,
    Docente,
    DocenteCurso,
    HorarioSlot,
    Inscripcion,
    Periodo,
)

admin.site.register(Alumno)
admin.site.register(Curso)
admin.site.register(Periodo)
admin.site.register(Inscripcion)
admin.site.register(Docente)
admin.site.register(DocenteCurso)
admin.site.register(ActaFinal)
admin.site.register(ActaRenglon)
admin.site.register(HorarioSlot)
