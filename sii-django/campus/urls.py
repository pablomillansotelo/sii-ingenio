from django.urls import path

from campus import views

urlpatterns = [
    path("", views.inicio, name="campus_inicio"),
    path("control-escolar/", views.control_escolar, name="campus_control_escolar"),
    path("calendario/", views.calendario, name="campus_calendario"),
    path("mensajes/", views.mensajes, name="campus_mensajes"),
    path("mensajes/<int:pk>/", views.hilo, name="campus_hilo"),
    path("mas/", views.mas, name="campus_mas"),
    path("datos/", views.ficha, name="campus_ficha"),
    path("avisos/", views.avisos, name="campus_avisos"),
    path("avisos/<int:aviso_id>/leer/", views.aviso_leer, name="campus_aviso_leer"),
    path("control-escolar/favorito/", views.favorito_toggle, name="campus_favorito"),
    path("kardex/", views.kardex, name="campus_kardex"),
    path("estado-cuenta/", views.estado_cuenta_view, name="campus_estado_cuenta"),
    path("noticias/<int:noticia_id>/", views.noticia_detalle, name="campus_noticia"),
    path("configuracion/", views.configuracion, name="campus_configuracion"),
    path("constancias/", views.constancias, name="campus_constancias"),
    path("constancias/pdf/", views.constancia_pdf, name="campus_constancia_pdf"),
    path("bajas/", views.bajas, name="campus_bajas"),
    path("expediente/", views.expediente, name="campus_expediente"),
    path("expediente/<int:pk>/archivo/", views.expediente_archivo, name="campus_expediente_archivo"),
    path("credencial/", views.credencial, name="campus_credencial"),
    path("aceptacion/", views.aceptacion, name="campus_aceptacion"),
    path("notificaciones/", views.notificaciones, name="campus_notificaciones"),
    path("notificaciones/<int:pk>/leer/", views.notificacion_leer, name="campus_notificacion_leer"),
    path("notificaciones/leer-todas/", views.notificaciones_leer_todas, name="campus_notificaciones_leer_todas"),
    path("progreso/", views.ludico, name="campus_ludico"),
]
