from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flashcards.models import Card
from flashcards.utils import update_card, get_next_card


class Command(BaseCommand):
    help = 'Prueba el algoritmo SM-2 con una tarjeta de ejemplo'
    
    def handle(self, *args, **options):
        # Obtener el primer usuario
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No hay usuarios en la base de datos'))
            return
        
        # Obtener la siguiente tarjeta
        card = get_next_card(user)
        
        if not card:
            self.stdout.write(self.style.WARNING('No hay tarjetas pendientes'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n📝 Tarjeta: {card.frente}'))
        self.stdout.write(f'Respuesta: {card.reverso}')
        self.stdout.write(f'Estado actual: {card.estado} | Fase: {card.fase}')
        self.stdout.write(f'Intervalo actual: {card.intervalo_actual}s')
        self.stdout.write(f'Aciertos: {card.contador_aciertos} | Fallos: {card.contador_fallos}')
        
        # Simular respuesta correcta rápida
        self.stdout.write(self.style.SUCCESS('\n✅ Simulando respuesta CORRECTA (calificación 5, 2 segundos)'))
        update_card(card, calificacion_base=5, tiempo_respuesta=2)
        
        card.refresh_from_db()
        self.stdout.write(f'Nuevo estado: {card.estado} | Fase: {card.fase}')
        self.stdout.write(f'Nuevo intervalo: {card.intervalo_actual}s')
        self.stdout.write(f'Próxima revisión: {card.siguiente_repeticion}')
        self.stdout.write(f'Aciertos: {card.contador_aciertos} | Fallos: {card.contador_fallos}')
