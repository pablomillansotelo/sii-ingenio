from django.contrib import admin
from sii.models import *  # Import your models here

# Register your models here.
admin.site.register(Alumno)
admin.site.register(Curso)
admin.site.register(Inscripcion)
admin.site.register(Periodo)