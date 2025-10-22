from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now

def get_fecha_hoy():
    return now().date()

class UserSettings(models.Model):
    """Configuración personal de cada usuario"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    max_tarjetas_nuevas_diarias = models.IntegerField(default=10)
    tarjetas_nuevas_hoy = models.IntegerField(default=0)
    ultima_fecha_reset = models.DateField(default=get_fecha_hoy)  
    
    class Meta:
        verbose_name = "Configuración de Usuario"
        verbose_name_plural = "Configuraciones de Usuarios"
    
    def __str__(self):
        return f"Config de {self.usuario.username}"
    
    def reset_contador_si_necesario(self):
        """Resetea el contador de tarjetas nuevas si es un nuevo día"""
        hoy = timezone.now().date()
        if self.ultima_fecha_reset < hoy:
            self.tarjetas_nuevas_hoy = 0
            self.ultima_fecha_reset = hoy
            self.save()

class Card(models.Model):
    """Tarjeta de estudio con sistema de repetición espaciada"""
    
    ESTADO_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('aprendizaje', 'Aprendizaje'),
        ('consolidacion', 'Consolidación'),
        ('maduro', 'Maduro'),
    ]
    
    FASE_CHOICES = [
        (1, 'Fase 1 - Aprendizaje Intensivo'),
        (2, 'Fase 2 - Consolidación'),
        (3, 'Fase 3 - Mantenimiento'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    frente = models.TextField(verbose_name="Pregunta")
    reverso = models.TextField(verbose_name="Respuesta")
    
    # Estado y fase
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='nuevo')
    fase = models.IntegerField(choices=FASE_CHOICES, default=1)
    
    # Algoritmo SM-2
    intervalo_actual = models.FloatField(default=5.0, help_text="Intervalo en segundos")
    EF = models.FloatField(default=2.5, verbose_name="Factor de Facilidad")
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_repeticion = models.DateTimeField(null=True, blank=True)
    siguiente_repeticion = models.DateTimeField(default=timezone.now)
    
    # Contadores
    contador_aciertos = models.IntegerField(default=0)
    contador_fallos = models.IntegerField(default=0)
    
    # Última respuesta
    tiempo_respuesta = models.FloatField(default=0.0, help_text="Tiempo en segundos")
    calificacion_ajustada = models.FloatField(default=0.0)
    
    class Meta:
        verbose_name = "Tarjeta"
        verbose_name_plural = "Tarjetas"
        ordering = ['siguiente_repeticion']
    
    def __str__(self):
        return f"{self.frente[:50]}..."
    
    def esta_vencida(self):
        """Verifica si la tarjeta necesita repaso"""
        return timezone.now() >= self.siguiente_repeticion
    
    def es_nueva(self):
        """Verifica si es una tarjeta nueva"""
        return self.estado == 'nuevo'


class ReviewLog(models.Model):
    """Historial de revisiones de cada tarjeta"""
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='reviews')
    fecha = models.DateTimeField(auto_now_add=True)
    
    # Calificaciones
    calificacion_base = models.IntegerField(help_text="Calificación 0-5 del usuario")
    tiempo_respuesta = models.FloatField(help_text="Tiempo en segundos")
    calificacion_ajustada = models.FloatField(help_text="Calificación ajustada por tiempo")
    
    # Fases
    fase_antes = models.IntegerField()
    fase_despues = models.IntegerField()
    
    class Meta:
        verbose_name = "Registro de Revisión"
        verbose_name_plural = "Registros de Revisiones"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Review {self.card.frente[:30]} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"


class Subscription(models.Model):
    """Suscripción a notificaciones push de cada usuario"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    endpoint = models.TextField(unique=True)
    p256dh = models.TextField(verbose_name="Clave P256DH")
    auth = models.TextField(verbose_name="Clave Auth")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Suscripción a Notificaciones"
        verbose_name_plural = "Suscripciones a Notificaciones"
    
    def __str__(self):
        return f"Suscripción de {self.usuario.username}"
