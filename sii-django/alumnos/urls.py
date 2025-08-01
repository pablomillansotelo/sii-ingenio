from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='dashboard'),
    path('kardex/', views.home, name='kardex'),
    path('alumnos/', views.home, name='alumnos'),
    path('horario/', views.home, name='horario'),
    path('home/', views.home, name='pagos'),
]