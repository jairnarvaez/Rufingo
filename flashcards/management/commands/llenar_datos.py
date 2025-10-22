import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

# Ajusta esta importación al nombre real de tu app
# Por ejemplo: from rufingo.models import UserSettings, Card, ReviewLog, Subscription
from flashcards.models import UserSettings, Card, ReviewLog, Subscription


class Command(BaseCommand):
    help = 'Llena la base de datos con datos de prueba (usuarios, settings, tarjetas y logs).'
    
    # Número de elementos a crear
    NUM_USERS = 5
    CARDS_PER_USER = 30
    REVIEWS_PER_CARD = 3 # Máximo de logs por tarjeta

    def handle(self, *args, **options):
        # Inicializar Faker y configurar timezone
        fake = Faker('es_ES')
        self.stdout.write(self.style.NOTICE(f"Iniciando la creación de {self.NUM_USERS} usuarios de prueba..."))

        # ----------------------------------------
        # 1. Crear Usuarios y UserSettings
        # ----------------------------------------
        
        # Eliminar datos existentes para empezar limpio (opcional, pero útil para pruebas)
        User.objects.filter(username__startswith='test_user_').delete()

        users = []
        for i in range(1, self.NUM_USERS + 1):
            username = f'test_user_{i}'
            email = f'user{i}@example.com'
            user, created = User.objects.get_or_create(
                username=username, 
                defaults={'email': email, 'is_staff': False, 'is_superuser': False}
            )
            user.set_password('12345') # Contraseña simple para pruebas
            user.save()
            users.append(user)

            # Crear UserSettings
            UserSettings.objects.get_or_create(
                usuario=user,
                defaults={
                    'max_tarjetas_nuevas_diarias': random.randint(5, 20),
                    'tarjetas_nuevas_hoy': random.randint(0, 5),
                    'ultima_fecha_reset': timezone.now().date() - timedelta(days=random.randint(0, 3)),
                }
            )

        self.stdout.write(self.style.SUCCESS(f'✅ {len(users)} Usuarios y UserSettings creados/actualizados.'))
        
        # ----------------------------------------
        # 2. Crear Tarjetas (Card)
        # ----------------------------------------
        
        all_cards = []
        estado_choices = [c[0] for c in Card.ESTADO_CHOICES]
        
        for user in users:
            for _ in range(self.CARDS_PER_USER):
                # Generar una fecha de próxima repetición en el pasado o futuro cercano
                siguiente_rep = timezone.now() + timedelta(days=random.uniform(-5, 7))
                
                # Asignar estado aleatorio
                estado = random.choice(estado_choices)
                
                # Simular EF y Intervalo
                ef = random.uniform(1.3, 2.5)
                intervalo = random.uniform(0.1, 90.0) # Días
                
                card = Card.objects.create(
                    usuario=user,
                    frente=fake.sentence(nb_words=6).replace('.', '?'),
                    reverso=fake.paragraph(nb_sentences=2),
                    estado=estado,
                    fase=random.choice([1, 2, 3]),
                    intervalo_actual=intervalo,
                    EF=ef,
                    ultima_repeticion=timezone.now() - timedelta(days=random.uniform(0, 30)),
                    siguiente_repeticion=siguiente_rep,
                    contador_aciertos=random.randint(0, 15),
                    contador_fallos=random.randint(0, 5),
                )
                all_cards.append(card)

        self.stdout.write(self.style.SUCCESS(f'✅ {len(all_cards)} Tarjetas creadas.'))

        # ----------------------------------------
        # 3. Crear Historial de Revisiones (ReviewLog)
        # ----------------------------------------

        all_logs = []
        for card in all_cards:
            num_logs = random.randint(0, self.REVIEWS_PER_CARD)
            fase_actual = card.fase
            
            for i in range(num_logs):
                calif_base = random.randint(1, 5)
                tiempo_resp = random.uniform(1.0, 15.0)
                calif_ajustada = calif_base * (1.0 - (tiempo_resp / 20.0)) # Simulación de ajuste
                
                fase_despues = fase_actual # Mantener la fase para el log
                if i == num_logs - 1: # Usar la fase real de la tarjeta en el último log
                    fase_despues = card.fase
                
                log = ReviewLog.objects.create(
                    card=card,
                    fecha=card.fecha_creacion + timedelta(days=random.uniform(1, 30)), # Fecha anterior a ahora
                    calificacion_base=calif_base,
                    tiempo_respuesta=tiempo_resp,
                    calificacion_ajustada=calif_ajustada,
                    fase_antes=fase_actual,
                    fase_despues=fase_despues,
                )
                all_logs.append(log)
                fase_actual = fase_despues # Simular cambio de fase

        self.stdout.write(self.style.SUCCESS(f'✅ {len(all_logs)} Registros de Revisión creados.'))

        # ----------------------------------------
        # 4. Crear Suscripciones (Subscription)
        # ----------------------------------------

        all_subscriptions = []
        for user in users:
             # Solo una probabilidad de que el usuario tenga suscripción
            if random.random() < 0.6: 
                endpoint = fake.url()
                
                # Las claves son strings Base64 simulados
                p256dh = fake.md5(raw_output=False)[:22] + '='
                auth = fake.md5(raw_output=False)[:12] + '='

                subscription = Subscription.objects.create(
                    usuario=user,
                    endpoint=f'https://fcm.googleapis.com/fcm/send/{endpoint}',
                    p256dh=p256dh,
                    auth=auth,
                )
                all_subscriptions.append(subscription)

        self.stdout.write(self.style.SUCCESS(f'✅ {len(all_subscriptions)} Suscripciones a Notificaciones creadas.'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 ¡Proceso de llenado de datos finalizado con éxito!'))
