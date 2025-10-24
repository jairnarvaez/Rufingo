from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from flashcards.models import Card, Subscription
from pywebpush import webpush, WebPushException
import json
import os


class Command(BaseCommand):
    help = 'Envía notificaciones push a usuarios con tarjetas pendientes'
    
    def handle(self, *args, **options):
        self.stdout.write('🔔 Verificando tarjetas pendientes...')
        
        ahora = timezone.now()
        notificaciones_enviadas = 0
        
        # Obtener usuarios con suscripciones activas
        usuarios_con_suscripcion = User.objects.filter(
            subscriptions__isnull=False
        ).distinct()
        
        for usuario in usuarios_con_suscripcion:
            # Contar tarjetas pendientes (vencidas)
            tarjetas_pendientes = Card.objects.filter(
                usuario=usuario,
                siguiente_repeticion__lte=ahora
            ).exclude(estado='nuevo').count()
            
            if tarjetas_pendientes > 0:
                # Enviar notificación a todas las suscripciones del usuario
                suscripciones = Subscription.objects.filter(usuario=usuario)
                
                for suscripcion in suscripciones:
                    try:
                        # Preparar mensaje
                        mensaje = {
                            "title": "🎓 Rufingo",
                            "body": f"¡Tienes {tarjetas_pendientes} tarjeta{'s' if tarjetas_pendientes > 1 else ''} pendiente{'s' if tarjetas_pendientes > 1 else ''} para repasar!",
                            "icon": "/static/android-chrome-192x192.png",
                            "badge": "/static/android-chrome-192x192.png",
                            "url": "/repaso/"
                        }
                        
                        # Configurar VAPID
                        vapid_private_key = os.getenv('VAPID_PRIVATE_KEY')
                        vapid_claims = {
                            "sub": f"mailto:{os.getenv('VAPID_CLAIM_EMAIL', 'admin@rufingo.com')}"
                        }
                        
                        # Enviar notificación
                        webpush(
                            subscription_info={
                                "endpoint": suscripcion.endpoint,
                                "keys": {
                                    "p256dh": suscripcion.p256dh,
                                    "auth": suscripcion.auth
                                }
                            },
                            data=json.dumps(mensaje),
                            vapid_private_key=vapid_private_key,
                            vapid_claims=vapid_claims
                        )
                        
                        notificaciones_enviadas += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Notificación enviada a {usuario.username} ({tarjetas_pendientes} tarjetas)'
                            )
                        )
                        
                    except WebPushException as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'❌ Error enviando notificación a {usuario.username}: {e}'
                            )
                        )
                        
                        # Si la suscripción es inválida (410 Gone), eliminarla
                        if e.response and e.response.status_code == 410:
                            suscripcion.delete()
                            self.stdout.write(
                                self.style.WARNING(
                                    f'🗑️ Suscripción inválida eliminada para {usuario.username}'
                                )
                            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado. {notificaciones_enviadas} notificación(es) enviada(s).'
            )
        )
