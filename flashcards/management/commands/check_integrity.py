from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flashcards.models import Card, UserSettings
from django.utils import timezone


class Command(BaseCommand):
    help = 'Verifica la integridad de los datos'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Verificando integridad de datos...\n')
        
        errores = 0
        warnings = 0
        
        # Verificar usuarios sin settings
        usuarios_sin_settings = User.objects.filter(settings__isnull=True)
        if usuarios_sin_settings.exists():
            errores += 1
            self.stdout.write(
                self.style.ERROR(
                    f'❌ {usuarios_sin_settings.count()} usuario(s) sin UserSettings'
                )
            )
            for user in usuarios_sin_settings:
                UserSettings.objects.create(usuario=user)
                self.stdout.write(f'   ✅ UserSettings creado para {user.username}')
        
        # Verificar tarjetas con intervalos negativos
        tarjetas_invalidas = Card.objects.filter(intervalo_actual__lt=0)
        if tarjetas_invalidas.exists():
            errores += 1
            self.stdout.write(
                self.style.ERROR(
                    f'❌ {tarjetas_invalidas.count()} tarjeta(s) con intervalos negativos'
                )
            )
            for card in tarjetas_invalidas:
                card.intervalo_actual = 5.0
                card.save()
                self.stdout.write(f'   ✅ Tarjeta {card.id} corregida')
        
        # Verificar tarjetas con EF inválido
        tarjetas_ef_invalido = Card.objects.filter(EF__lt=1.3)
        if tarjetas_ef_invalido.exists():
            warnings += 1
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  {tarjetas_ef_invalido.count()} tarjeta(s) con EF < 1.3'
                )
            )
            for card in tarjetas_ef_invalido:
                card.EF = 1.3
                card.save()
                self.stdout.write(f'   ✅ Tarjeta {card.id} corregida (EF = 1.3)')
        
        # Verificar tarjetas sin siguiente_repeticion
        tarjetas_sin_fecha = Card.objects.filter(siguiente_repeticion__isnull=True)
        if tarjetas_sin_fecha.exists():
            errores += 1
            self.stdout.write(
                self.style.ERROR(
                    f'❌ {tarjetas_sin_fecha.count()} tarjeta(s) sin siguiente_repeticion'
                )
            )
            for card in tarjetas_sin_fecha:
                card.siguiente_repeticion = timezone.now()
                card.save()
                self.stdout.write(f'   ✅ Tarjeta {card.id} corregida')
        
        # Verificar estados inconsistentes
        estados_validos = ['nuevo', 'aprendizaje', 'consolidacion', 'maduro']
        tarjetas_estado_invalido = Card.objects.exclude(estado__in=estados_validos)
        if tarjetas_estado_invalido.exists():
            errores += 1
            self.stdout.write(
                self.style.ERROR(
                    f'❌ {tarjetas_estado_invalido.count()} tarjeta(s) con estado inválido'
                )
            )
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        if errores == 0 and warnings == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ Todo está en orden. No se encontraron problemas.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Se encontraron {errores} error(es) y {warnings} advertencia(s)'
                )
            )
        self.stdout.write('='*60 + '\n')
