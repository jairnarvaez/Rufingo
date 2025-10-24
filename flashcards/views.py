from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Card, UserSettings, ReviewLog, Subscription 
from .utils import get_next_card, update_card
from django.utils import timezone
from django.views.decorators.http import require_POST
import json
import os
from django.conf import settings

from django.contrib.auth import logout
from django.shortcuts import redirect
from flashcards.models import Subscription

@login_required
def home(request):
    """Vista principal - Dashboard"""
    user = request.user
    
    # Obtener estadísticas
    total_tarjetas = Card.objects.filter(usuario=user).count()
    tarjetas_aprendizaje = Card.objects.filter(usuario=user, estado='aprendizaje').count()
    tarjetas_consolidacion = Card.objects.filter(usuario=user, estado='consolidacion').count()
    tarjetas_maduras = Card.objects.filter(usuario=user, estado='maduro').count()
    
    # Tarjetas pendientes (vencidas)
    ahora = timezone.now()
    tarjetas_pendientes = Card.objects.filter(
        usuario=user,
        siguiente_repeticion__lte=ahora
    ).exclude(estado='nuevo').count()

    # Settings del usuario
    settings = user.settings
    settings.reset_contador_si_necesario()
    
    context = {
        'total_tarjetas': total_tarjetas,
        'tarjetas_aprendizaje': tarjetas_aprendizaje,
        'tarjetas_consolidacion': tarjetas_consolidacion,
        'tarjetas_maduras': tarjetas_maduras,
        'tarjetas_pendientes': tarjetas_pendientes,
        'tarjetas_nuevas_hoy': settings.tarjetas_nuevas_hoy,
        'max_tarjetas_nuevas': settings.max_tarjetas_nuevas_diarias,
    }

    print(context)
    
    return render(request, 'flashcards/home.html', context)


@login_required
def lista_tarjetas(request):
    """Vista para listar todas las tarjetas con filtros"""
    user = request.user
    
    # Filtros
    filtro_estado = request.GET.get('estado', '')
    filtro_fase = request.GET.get('fase', '')
    busqueda = request.GET.get('q', '')
    
    tarjetas = Card.objects.filter(usuario=user)
    
    if filtro_estado:
        tarjetas = tarjetas.filter(estado=filtro_estado)
    
    if filtro_fase:
        tarjetas = tarjetas.filter(fase=int(filtro_fase))
    
    if busqueda:
        tarjetas = tarjetas.filter(frente__icontains=busqueda) | tarjetas.filter(reverso__icontains=busqueda)
    
    tarjetas = tarjetas.order_by('-fecha_creacion')
    
    context = {
        'tarjetas': tarjetas,
        'filtro_estado': filtro_estado,
        'filtro_fase': filtro_fase,
        'busqueda': busqueda,
    }
    
    return render(request, 'flashcards/lista_tarjetas.html', context)


@login_required
def crear_tarjeta(request):
    """Vista para crear una nueva tarjeta"""
    if request.method == 'POST':
        frente = request.POST.get('frente', '').strip()
        reverso = request.POST.get('reverso', '').strip()
        
        if not frente or not reverso:
            messages.error(request, 'Ambos campos son obligatorios.')
            return render(request, 'flashcards/crear_tarjeta.html')

        usuario = request.user
        settings = usuario.settings
        settings.reset_contador_si_necesario()
        settings.tarjetas_nuevas_hoy += 1
        
        if settings.tarjetas_nuevas_hoy > settings.max_tarjetas_nuevas_diarias:
            messages.error(request, 'Límite de tarjetas diarias alcanzado')
            return render(request, 'flashcards/crear_tarjeta.html')
            
        settings.save()

        # Crear la tarjeta
        Card.objects.create(
            usuario=request.user,
            frente=frente,
            reverso=reverso,
            estado='aprendizaje',
            siguiente_repeticion=timezone.now()
        )
        
        messages.success(request, '✅ Tarjeta creada exitosamente.')
        return redirect('crear_tarjeta')
    
    return render(request, 'flashcards/crear_tarjeta.html')


@login_required
def editar_tarjeta(request, card_id):
    """Vista para editar una tarjeta existente"""
    tarjeta = get_object_or_404(Card, id=card_id, usuario=request.user)
    
    if request.method == 'POST':
        frente = request.POST.get('frente', '').strip()
        reverso = request.POST.get('reverso', '').strip()
        
        if not frente or not reverso:
            messages.error(request, 'Ambos campos son obligatorios.')
            return render(request, 'flashcards/editar_tarjeta.html', {'tarjeta': tarjeta})
        
        tarjeta.frente = frente
        tarjeta.reverso = reverso
        tarjeta.save()
        
        messages.success(request, '✅ Tarjeta actualizada exitosamente.')
        return redirect('lista_tarjetas')
    
    return render(request, 'flashcards/editar_tarjeta.html', {'tarjeta': tarjeta})


@login_required
def eliminar_tarjeta(request, card_id):
    """Vista para eliminar una tarjeta"""
    tarjeta = get_object_or_404(Card, id=card_id, usuario=request.user)
    
    if request.method == 'POST':
        tarjeta.delete()
        messages.success(request, '🗑️ Tarjeta eliminada exitosamente.')
        return redirect('lista_tarjetas')
    
    return render(request, 'flashcards/eliminar_tarjeta.html', {'tarjeta': tarjeta})


@login_required
def reiniciar_tarjeta(request, card_id):
    """Vista para reiniciar el progreso de una tarjeta"""
    tarjeta = get_object_or_404(Card, id=card_id, usuario=request.user)
    
    if request.method == 'POST':
        tarjeta.estado = 'nuevo'
        tarjeta.fase = 1
        tarjeta.intervalo_actual = 5.0
        tarjeta.EF = 2.5
        tarjeta.contador_aciertos = 0
        tarjeta.contador_fallos = 0
        tarjeta.siguiente_repeticion = timezone.now()
        tarjeta.save()
        
        messages.success(request, '🔄 Progreso de la tarjeta reiniciado.')
        return redirect('lista_tarjetas')
    
    return render(request, 'flashcards/reiniciar_tarjeta.html', {'tarjeta': tarjeta})


@login_required
def estadisticas(request):
    """Vista de estadísticas detalladas"""
    user = request.user
    
    # Estadísticas generales
    total_tarjetas = Card.objects.filter(usuario=user).count()
    
    # Por fase
    fase_1 = Card.objects.filter(usuario=user, fase=1).count()
    fase_2 = Card.objects.filter(usuario=user, fase=2).count()
    fase_3 = Card.objects.filter(usuario=user, fase=3).count()
    
    # Por estado
    nuevas = Card.objects.filter(usuario=user, estado='nuevo').count()
    aprendizaje = Card.objects.filter(usuario=user, estado='aprendizaje').count()
    consolidacion = Card.objects.filter(usuario=user, estado='consolidacion').count()
    maduras = Card.objects.filter(usuario=user, estado='maduro').count()
    
    # Tarjetas pendientes hoy
    ahora = timezone.now()
    pendientes_hoy = Card.objects.filter(
        usuario=user,
        siguiente_repeticion__lte=ahora
    ).exclude(estado='nuevo').count()
    
    context = {
        'total_tarjetas': total_tarjetas,
        'fase_1': fase_1,
        'fase_2': fase_2,
        'fase_3': fase_3,
        'nuevas': nuevas,
        'aprendizaje': aprendizaje,
        'consolidacion': consolidacion,
        'maduras': maduras,
        'pendientes_hoy': pendientes_hoy,
    }
    
    return render(request, 'flashcards/estadisticas.html', context)

@login_required
def sesion_repaso(request):
    """Vista principal de la sesión de repaso"""
    user = request.user
    
    # Obtener la siguiente tarjeta
    card = get_next_card(user)
    
    if not card:
        # No hay tarjetas pendientes
        return render(request, 'flashcards/sin_tarjetas.html')
    
    context = {
        'card': card,
    }
    
    return render(request, 'flashcards/sesion_repaso.html', context)


@login_required
@require_POST
def procesar_respuesta(request):
    """Procesa la respuesta del usuario a una tarjeta"""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        calificacion_base = int(data.get('calificacion_base'))
        tiempo_respuesta = float(data.get('tiempo_respuesta'))
        
        # Validar datos
        if not card_id or calificacion_base < 0 or calificacion_base > 5:
            return JsonResponse({'error': 'Datos inválidos'}, status=400)
        
        # Obtener tarjeta
        card = get_object_or_404(Card, id=card_id, usuario=request.user)
        
        # Actualizar tarjeta
        update_card(card, calificacion_base, tiempo_respuesta)
        
        # Obtener siguiente tarjeta
        siguiente_card = get_next_card(request.user)
        
        response_data = {
            'success': True,
            'mensaje': '✅ Respuesta registrada',
            'siguiente_tarjeta': siguiente_card.id if siguiente_card else None,
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def resultado_repaso(request):
    """Vista de resultados después de completar el repaso"""
    return render(request, 'flashcards/resultado_repaso.html')

def tarjetas_pendientes_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'pendientes': 0})

    pendientes = Card.objects.filter(
        usuario=request.user,
        siguiente_repeticion__lte=timezone.now()
    ).exclude(estado='nuevo').count()

    return JsonResponse({'pendientes': pendientes})


@login_required
@require_POST
def guardar_suscripcion(request):
    """Guarda la suscripción de notificaciones push del usuario"""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        p256dh = data.get('keys', {}).get('p256dh')
        auth = data.get('keys', {}).get('auth')
        
        if not endpoint or not p256dh or not auth:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        # Crear o actualizar suscripción
        subscription, created = Subscription.objects.get_or_create(
            usuario=request.user,
            endpoint=endpoint,
            defaults={'p256dh': p256dh, 'auth': auth}
        )
        
        if not created:
            subscription.p256dh = p256dh
            subscription.auth = auth
            subscription.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': '✅ Notificaciones activadas correctamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def configuracion_notificaciones(request):
    """Vista para configurar notificaciones"""
    # Verificar si el usuario tiene suscripciones activas
    tiene_suscripcion = Subscription.objects.filter(usuario=request.user).exists()
    
    context = {
        'tiene_suscripcion': tiene_suscripcion,
        'vapid_public_key': "BEfSLf_2i2z9fKWCyBrGzhWSNMa2DfOZR4exivUaapIH5QklCsTOQ9Cv-JRzQrbzVqIkkZ6hin3CYAeHeuI4flM=",
    }
    
    return render(request, 'flashcards/configuracion_notificaciones.html', context)

def logout_view(request):
    """Cierra sesión y borra las suscripciones push del usuario"""
    if request.user.is_authenticated:
        Subscription.objects.filter(usuario=request.user).delete()
    logout(request)
    return redirect('home')
