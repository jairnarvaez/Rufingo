from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Card, UserSettings
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
        # Tiempo rápido (0-3s): sin ajuste
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 2), 5.0)
        
        # Tiempo medio (3-6s): -0.5
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 5), 4.5)
        
        # Tiempo lento (6-10s): -1
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 8), 4.0)
        
        # Tiempo muy lento (>10s): -2
        self.assertEqual(ajustar_calificacion_por_tiempo(5, 15), 3.0)
    
    def test_calculo_nuevo_EF(self):
        """Test de cálculo del factor de facilidad"""
        EF_inicial = 2.5
        
        # Calificación alta debería aumentar EF
        nuevo_EF = calcular_nuevo_EF(EF_inicial, 5)
        self.assertGreater(nuevo_EF, EF_inicial)
        
        # Calificación baja debería disminuir EF
        nuevo_EF = calcular_nuevo_EF(EF_inicial, 2)
        self.assertLess(nuevo_EF, EF_inicial)
        
        # EF nunca debe ser menor a 1.3
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
        self.assertEqual(self.card.intervalo_actual, 5.0)  # Vuelve al primer intervalo
    
    def test_get_next_card_prioridad(self):
        """Test de prioridad de tarjetas"""
        # Crear tarjeta vencida
        tarjeta_vencida = Card.objects.create(
            usuario=self.user,
            frente='Pregunta vencida',
            reverso='Respuesta',
            estado='aprendizaje',
            siguiente_repeticion=timezone.now() - timezone.timedelta(hours=1)
        )
        
        # La tarjeta vencida debe tener prioridad
        siguiente = get_next_card(self.user)
        self.assertEqual(siguiente.id, tarjeta_vencida.id)
    
    def test_limite_tarjetas_nuevas_diarias(self):
        """Test del límite de 10 tarjetas nuevas por día"""
        # Crear 11 tarjetas nuevas
        for i in range(11):
            Card.objects.create(
                usuario=self.user,
                frente=f'Pregunta {i}',
                reverso=f'Respuesta {i}'
            )
        
        # Obtener 10 tarjetas (máximo permitido)
        for i in range(10):
            card = get_next_card(self.user)
            self.assertIsNotNone(card)
            card.estado = 'aprendizaje'
            card.save()
        
        # La tarjeta 11 no debería estar disponible hoy
        card = get_next_card(self.user)
        # Podría ser None o la tarjeta original self.card
        if card:
            self.assertNotEqual(card.estado, 'nuevo')
