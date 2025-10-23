from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from .models import Card, UserSettings, ReviewLog, Subscription
from .utils import (
    ajustar_calificacion_por_tiempo,
    calcular_nuevo_EF,
    update_card,
    get_next_card
)


class SM2LogicTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.card = Card.objects.create(
            usuario=self.user,
            frente='¿Cuál es la capital de Francia?',
            reverso='París'
        )
    
    def test_ajuste_calificacion_por_tiempo(self):
        """Test de ajuste de calificación según tiempo"""
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 2), 5.0)
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 5), 4.5)
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 8), 4.0)
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 15), 3.0)
    
    def test_calculo_nuevo_EF(self):
        """Test de cálculo del factor de facilidad"""
        EF_inicial = 2.5
        nuevo_EF = calcular_nuevo_EF(EF_inicial, 5)
        self.assertGreater(nuevo_EF, EF_inicial)
        
        nuevo_EF = calcular_nuevo_EF(EF_inicial, 2)
        self.assertLess(nuevo_EF, EF_inicial)
        
        nuevo_EF = calcular_nuevo_EF(1.3, 0)
        self.assertGreaterEqual(nuevo_EF, 1.3)
    
    def test_update_card_respuesta_correcta(self):
        """Test de actualización con respuesta correcta"""
        update_card(self.card, calificacion_base=5, tiempo_respuesta=2)
        
        self.card.refresh_from_db()
        self.assertEqual(self.card.contador_aciertos, 1)
        self.assertEqual(self.card.contador_fallos, 0)
        self.assertEqual(self.card.estado, 'aprendizaje')
        self.assertIsNotNone(self.card.siguiente_repeticion)
    
    def test_update_card_respuesta_incorrecta(self):
        """Test de actualización con respuesta incorrecta"""
        update_card(self.card, calificacion_base=1, tiempo_respuesta=15)
        
        self.card.refresh_from_db()
        self.assertEqual(self.card.contador_fallos, 1)
        self.assertEqual(self.card.contador_aciertos, 0)
        self.assertEqual(self.card.intervalo_actual, 5.0)
    
    def test_get_next_card_prioridad(self):
        """Test de prioridad de tarjetas"""
        tarjeta_vencida = Card.objects.create(
            usuario=self.user,
            frente='Pregunta vencida',
            reverso='Respuesta',
            estado='aprendizaje',
            siguiente_repeticion=timezone.now() - timezone.timedelta(hours=1)
        )
        
        siguiente = get_next_card(self.user)
        self.assertEqual(siguiente.id, tarjeta_vencida.id)
    
    def test_limite_tarjetas_nuevas_diarias(self):
        """Test del límite de 10 tarjetas nuevas por día"""
        for i in range(11):
            Card.objects.create(
                usuario=self.user,
                frente=f'Pregunta {i}',
                reverso=f'Respuesta {i}'
            )
        
        for i in range(10):
            card = get_next_card(self.user)
            self.assertIsNotNone(card)
            card.estado = 'aprendizaje'
            card.save()
        
        card = get_next_card(self.user)
        if card:
            self.assertNotEqual(card.estado, 'nuevo')


class ViewsTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
    
    def test_home_view(self):
        """Test de la vista home"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_crear_tarjeta(self):
        """Test de creación de tarjeta"""
        response = self.client.post(reverse('crear_tarjeta'), {
            'frente': 'Test pregunta',
            'reverso': 'Test respuesta'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(Card.objects.filter(frente='Test pregunta').exists())
    
    def test_editar_tarjeta(self):
        """Test de edición de tarjeta"""
        card = Card.objects.create(
            usuario=self.user,
            frente='Pregunta original',
            reverso='Respuesta original'
        )
        
        response = self.client.post(reverse('editar_tarjeta', args=[card.id]), {
            'frente': 'Pregunta editada',
            'reverso': 'Respuesta editada'
        })
        
        card.refresh_from_db()
        self.assertEqual(card.frente, 'Pregunta editada')
    
    def test_eliminar_tarjeta(self):
        """Test de eliminación de tarjeta"""
        card = Card.objects.create(
            usuario=self.user,
            frente='Pregunta a eliminar',
            reverso='Respuesta'
        )
        
        response = self.client.post(reverse('eliminar_tarjeta', args=[card.id]))
        self.assertFalse(Card.objects.filter(id=card.id).exists())
    
    def test_sesion_repaso_sin_tarjetas(self):
        """Test de sesión de repaso sin tarjetas pendientes"""
        response = self.client.get(reverse('sesion_repaso'))
        self.assertContains(response, 'Sin Tarjetas')
    
    def test_login_requerido(self):
        """Test de que las vistas requieren login"""
        self.client.logout()
        
        views_protegidas = [
            'home', 'lista_tarjetas', 'crear_tarjeta', 
            'estadisticas', 'sesion_repaso', 'configuracion_notificaciones'
        ]
        
        for view_name in views_protegidas:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 302)  # Redirect a login
            self.assertIn('/login/', response.url)


class UserSettingsTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
    
    def test_user_settings_creado_automaticamente(self):
        """Test de que UserSettings se crea automáticamente"""
        self.assertTrue(hasattr(self.user, 'settings'))
        self.assertEqual(self.user.settings.max_tarjetas_nuevas_diarias, 10)
    
    def test_reset_contador_diario(self):
        """Test de reseteo de contador diario"""
        settings = self.user.settings
        settings.tarjetas_nuevas_hoy = 5
        settings.ultima_fecha_reset = timezone.now().date() - timezone.timedelta(days=1)
        settings.save()
        
        settings.reset_contador_si_necesario()
        
        self.assertEqual(settings.tarjetas_nuevas_hoy, 0)
        self.assertEqual(settings.ultima_fecha_reset, timezone.now().date())
