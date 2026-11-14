from django.urls import path

from campus import views

urlpatterns = [
    path("", views.inicio, name="campus_inicio"),
    path("control-escolar/", views.control_escolar, name="campus_control_escolar"),
    path("calendario/", views.calendario, name="campus_calendario"),
    path("mensajes/", views.mensajes, name="campus_mensajes"),
    path("mas/", views.mas, name="campus_mas"),
    path("datos/", views.ficha, name="campus_ficha"),
    path("avisos/", views.avisos, name="campus_avisos"),
    path("avisos/<int:aviso_id>/leer/", views.aviso_leer, name="campus_aviso_leer"),
    path("control-escolar/favorito/", views.favorito_toggle, name="campus_favorito"),
    path("kardex/", views.kardex, name="campus_kardex"),
    path("estado-cuenta/", views.estado_cuenta_view, name="campus_estado_cuenta"),
    path("noticias/<int:noticia_id>/", views.noticia_detalle, name="campus_noticia"),
]
