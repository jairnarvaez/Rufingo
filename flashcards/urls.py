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
    
    # Rutas de repaso
    path('repaso/', views.sesion_repaso, name='sesion_repaso'),
    path('api/respuesta/', views.procesar_respuesta, name='procesar_respuesta'),
    path('repaso/completado/', views.resultado_repaso, name='resultado_repaso'),
    
    path('api/tarjetas_pendientes/', views.tarjetas_pendientes_api, name='tarjetas_pendientes_api'),

]
