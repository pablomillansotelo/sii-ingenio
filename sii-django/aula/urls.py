from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="aula_dashboard"),
    path("kardex/", views.kardex, name="aula_kardex"),
]
