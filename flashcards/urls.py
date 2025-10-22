from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tarjetas/', views.lista_tarjetas, name='lista_tarjetas'),
    path('tarjetas/crear/', views.crear_tarjeta, name='crear_tarjeta'),
    path('tarjetas/<int:card_id>/editar/', views.editar_tarjeta, name='editar_tarjeta'),
    path('tarjetas/<int:card_id>/eliminar/', views.eliminar_tarjeta, name='eliminar_tarjeta'),
    path('tarjetas/<int:card_id>/reiniciar/', views.reiniciar_tarjeta, name='reiniciar_tarjeta'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]
