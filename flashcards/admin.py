from django.contrib import admin
from .models import Card, ReviewLog, Subscription, UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'max_tarjetas_nuevas_diarias', 'tarjetas_nuevas_hoy', 'ultima_fecha_reset']
    list_filter = ['ultima_fecha_reset']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['frente_corto', 'usuario', 'estado', 'fase', 'siguiente_repeticion', 'contador_aciertos', 'contador_fallos']
    list_filter = ['estado', 'fase', 'usuario']
    search_fields = ['frente', 'reverso']
    readonly_fields = ['fecha_creacion', 'ultima_repeticion']
    
    def frente_corto(self, obj):
        return obj.frente[:50] + '...' if len(obj.frente) > 50 else obj.frente
    frente_corto.short_description = 'Pregunta'


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ['card', 'fecha', 'calificacion_base', 'tiempo_respuesta', 'fase_antes', 'fase_despues']
    list_filter = ['fecha', 'fase_antes', 'fase_despues']
    readonly_fields = ['fecha']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'fecha_creacion', 'endpoint_corto']
    list_filter = ['fecha_creacion']
    readonly_fields = ['fecha_creacion']
    
    def endpoint_corto(self, obj):
        return obj.endpoint[:50] + '...'
    endpoint_corto.short_description = 'Endpoint'
