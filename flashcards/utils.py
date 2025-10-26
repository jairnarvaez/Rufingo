from datetime import timedelta
from django.utils import timezone
from .models import Card, ReviewLog


# Intervalos para cada fase (en segundos)
INTERVALOS_FASE_1 = [5, 25, 120, 600]  # 5s, 25s, 2min, 10min
INTERVALOS_FASE_2 = [86400, 259200, 604800, 1209600]  # 1d, 3d, 7d, 14d


def ajustar_calificacion_por_tiempo(calificacion_base, tiempo_respuesta):
    """
    Ajusta la calificación base según el tiempo de respuesta
    
    Calificación base (0-5):
    5 = Perfecto, respuesta inmediata
    4 = Correcta con ligera vacilación
    3 = Correcta con esfuerzo
    2 = Incorrecta, pero algo recordada
    1 = Incorrecta, sin recuerdo
    0 = Olvido total
    
    Ajuste por tiempo:
    0-3s: +0
    3-6s: -0.5
    6-10s: -1
    >10s: -2
    """

    """
    De momento no voy a realizar el ajuste de calificacion por tiempo, queda para implementaciones futuras
    """

    """
    if tiempo_respuesta <= 3:
        ajuste = 0
    elif tiempo_respuesta <= 6:
        ajuste = -0.5
    elif tiempo_respuesta <= 10:
        ajuste = -1
    else:
        ajuste = -2
    """

    ajuste = 0
    
    calificacion_ajustada = max(0, min(5, calificacion_base + ajuste))
    return calificacion_ajustada


def calcular_nuevo_EF(EF_actual, calificacion_ajustada):
    """
    Calcula el nuevo factor de facilidad según SM-2
    EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    donde q es la calificación (0-5)
    """
    nuevo_EF = EF_actual + (0.1 - (5 - calificacion_ajustada) * (0.08 + (5 - calificacion_ajustada) * 0.02))
    # EF mínimo es 1.3
    return max(1.3, nuevo_EF)


def calcular_siguiente_intervalo_fase_1(card, es_correcto):
    """
    Calcula el siguiente intervalo para Fase 1 (Aprendizaje Intensivo)
    """
    if not es_correcto:
        # Si falla, vuelve al primer intervalo
        return INTERVALOS_FASE_1[0]
    
    # Buscar índice actual
    try:
        indice_actual = INTERVALOS_FASE_1.index(int(card.intervalo_actual))
    except ValueError:
        indice_actual = 0
    
    # Avanzar al siguiente intervalo
    indice_siguiente = min(indice_actual + 1, len(INTERVALOS_FASE_1) - 1)
    return INTERVALOS_FASE_1[indice_siguiente]


def calcular_siguiente_intervalo_fase_2(card, calificacion_ajustada):
    """
    Calcula el siguiente intervalo para Fase 2 (Consolidación)
    Usa intervalos predefinidos pero considera la calificación
    """
    if calificacion_ajustada < 3:
        # Si falla, retrocede a Fase 1
        return None  # Indicador para retroceder
    
    # Buscar índice actual en intervalos de Fase 2
    try:
        indice_actual = INTERVALOS_FASE_2.index(int(card.intervalo_actual))
    except ValueError:
        # Si no está en la lista, empezar desde el principio
        return INTERVALOS_FASE_2[0]
    
    # Avanzar al siguiente intervalo
    if indice_actual < len(INTERVALOS_FASE_2) - 1:
        return INTERVALOS_FASE_2[indice_actual + 1]
    else:
        # Si completó todos los intervalos, usar SM-2 para calcular
        return card.intervalo_actual * card.EF


def calcular_siguiente_intervalo_fase_3(card):
    """
    Calcula el siguiente intervalo para Fase 3 (Mantenimiento)
    Usa el algoritmo SM-2 completo
    """
    return card.intervalo_actual * card.EF


def verificar_promocion_fase_1_a_2(card):
    """
    Verifica si la tarjeta puede promocionar de Fase 1 a Fase 2
    Condiciones:
    - 3 aciertos consecutivos
    - Tiempo promedio < 4 segundos
    - Completó al menos el intervalo de 10 minutos
    """
    if card.contador_aciertos >= 3 and card.intervalo_actual >= 600:
        # Calcular tiempo promedio de las últimas 3 revisiones
        ultimas_reviews = card.reviews.order_by('-fecha')[:3]
        if ultimas_reviews.count() >= 3:
            tiempo_promedio = sum(r.tiempo_respuesta for r in ultimas_reviews) / 3
            if tiempo_promedio < 4:
                return True
    return False


def verificar_promocion_fase_2_a_3(card):
    """
    Verifica si la tarjeta puede promocionar de Fase 2 a Fase 3
    Condiciones:
    - Completó 3-5 intervalos sin fallos
    - Está en el último intervalo de Fase 2 o más
    """
    if card.contador_aciertos >= 3 and card.intervalo_actual >= INTERVALOS_FASE_2[-1]:
        return True
    return False


def aplicar_transicion_fase(card, calificacion_ajustada):
    """
    Aplica las transiciones entre fases según el rendimiento
    """
    fase_anterior = card.fase
    
    if card.fase == 1:
        # Verificar promoción a Fase 2
        if verificar_promocion_fase_1_a_2(card):
            card.fase = 2
            card.estado = 'consolidacion'
            card.intervalo_actual = INTERVALOS_FASE_2[0]  # Empezar con 1 día
            card.contador_aciertos = 0  # Resetear contador
            print(f"✅ Tarjeta promocionada a Fase 2")
    
    elif card.fase == 2:
        # Verificar retroceso a Fase 1
        if calificacion_ajustada < 3 or (calificacion_ajustada < 4 and card.tiempo_respuesta > 10):
            card.fase = 1
            card.estado = 'aprendizaje'
            card.intervalo_actual = INTERVALOS_FASE_1[0]
            card.contador_aciertos = 0
            print(f"⬇️ Tarjeta retrocedió a Fase 1")
        # Verificar promoción a Fase 3
        elif verificar_promocion_fase_2_a_3(card):
            card.fase = 3
            card.estado = 'maduro'
            card.intervalo_actual = 2592000  # 30 días en segundos
            card.contador_aciertos = 0
            print(f"✅ Tarjeta promocionada a Fase 3")
    
    elif card.fase == 3:
        # Verificar retroceso a Fase 2
        if calificacion_ajustada < 3:
            card.fase = 2
            card.estado = 'consolidacion'
            card.intervalo_actual = INTERVALOS_FASE_2[0]
            card.contador_aciertos = 0
            print(f"⬇️ Tarjeta retrocedió a Fase 2")
    
    return fase_anterior


def update_card(card, calificacion_base, tiempo_respuesta):
    """
    Función principal que actualiza una tarjeta después de una revisión
    """
    # 1. Ajustar calificación por tiempo
    calificacion_ajustada = ajustar_calificacion_por_tiempo(calificacion_base, tiempo_respuesta)
    
    # 2. Actualizar EF solo si la calificación es >= 3
    if calificacion_ajustada >= 3:
        card.EF = calcular_nuevo_EF(card.EF, calificacion_ajustada)
    
    # 3. Actualizar contadores
    if calificacion_ajustada >= 4:
        card.contador_aciertos += 1
        card.contador_fallos = 0  # Resetear fallos
    else:
        card.contador_fallos += 1
        card.contador_aciertos = 0  # Resetear aciertos
    
    # 4. Guardar datos de la última respuesta
    card.tiempo_respuesta = tiempo_respuesta
    card.calificacion_ajustada = calificacion_ajustada
    card.ultima_repeticion = timezone.now()
    
    # 5. Aplicar transiciones de fase
    fase_anterior = aplicar_transicion_fase(card, calificacion_ajustada)

    # Si cambió de fase, no recalcular el intervalo en esta misma llamada
    if card.fase != fase_anterior:
        card.siguiente_repeticion = timezone.now() + timedelta(seconds=card.intervalo_actual)
        card.save()
        ReviewLog.objects.create(
            card=card,
            calificacion_base=calificacion_base,
            tiempo_respuesta=tiempo_respuesta,
            calificacion_ajustada=calificacion_ajustada,
            fase_antes=fase_anterior,
            fase_despues=card.fase,
        )
        return card
    
    # 6. Calcular siguiente intervalo según la fase
    nuevo_intervalo = None
    
    if card.fase == 1:
        es_correcto = calificacion_ajustada >= 4
        nuevo_intervalo = calcular_siguiente_intervalo_fase_1(card, es_correcto)
    
    elif card.fase == 2:
        nuevo_intervalo = calcular_siguiente_intervalo_fase_2(card, calificacion_ajustada)
        if nuevo_intervalo is None:
            # Retroceder a Fase 1
            card.fase = 1
            card.estado = 'aprendizaje'
            nuevo_intervalo = INTERVALOS_FASE_1[0]
            card.contador_aciertos = 0
    
    elif card.fase == 3:
        nuevo_intervalo = calcular_siguiente_intervalo_fase_3(card)
    
    # 7. Actualizar intervalo y siguiente repetición
    card.intervalo_actual = nuevo_intervalo
    card.siguiente_repeticion = timezone.now() + timedelta(seconds=nuevo_intervalo)
    
    # 8. Cambiar estado si es necesario
    if card.estado == 'nuevo':
        card.estado = 'aprendizaje'
    
    # 9. Guardar la tarjeta
    card.save()
    
    # 10. Registrar en el historial
    ReviewLog.objects.create(
        card=card,
        calificacion_base=calificacion_base,
        tiempo_respuesta=tiempo_respuesta,
        calificacion_ajustada=calificacion_ajustada,
        fase_antes=fase_anterior,
        fase_despues=card.fase
    )
    
    return card


def get_next_card(usuario):
    """
    Obtiene la siguiente tarjeta a revisar según prioridades:
    1. Tarjetas vencidas (siguiente_repeticion <= ahora)
    2. Tarjetas nuevas (si no alcanzó límite diario)
    3. None si no hay nada pendiente
    """
    ahora = timezone.now()
    
    # Prioridad 1: Tarjetas vencidas
    tarjeta_vencida = Card.objects.filter(
        usuario=usuario,
        siguiente_repeticion__lte=ahora
    ).exclude(estado='nuevo').first()
    
    if tarjeta_vencida:
        return tarjeta_vencida
    
    return None
