"""
CONFIGURACIÓN AVANZADA Y SEGURIDAD DEL KANBAN BOARD

Este archivo contiene:
1. Decoradores personalizados
2. Configuración de permisos
3. Rate limiting
4. Caching
5. Validaciones personalizadas
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 1. DECORADORES PERSONALIZADOS
# ============================================================================

def solo_jefes(view_func):
    """
    Decorador que permite acceso solo a usuarios con rol 'jefe'.
    Verifica si el usuario tiene el permiso 'es_jefe' en su perfil.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar si es jefe (implementa tu lógica de rol)
        if not hasattr(request.user, 'profile') or not request.user.profile.es_jefe:
            logger.warning(f"Acceso denegado a {request.user} en {view_func.__name__}")
            return JsonResponse({
                'success': False,
                'error': 'Solo jefes pueden acceder a esta función'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def solo_personal_autorizado(view_func):
    """
    Decorador que permite acceso a usuarios autorizados en el módulo paneltareas.
    Útil para vistas que modifican datos sensibles.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Verificar permisos específicos
        if not request.user.groups.filter(name='Personal_Tareas').exists():
            if not request.user.is_staff and not request.user.is_superuser:
                logger.warning(f"Acceso no autorizado: {request.user}")
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para esta acción'
                }, status=403)
        
        logger.info(f"Acceso autorizado a {request.user} en {view_func.__name__}")
        return view_func(request, *args, **kwargs)
    
    return wrapper


def rate_limit(calls=100, period=3600):
    """
    Decorador que implementa rate limiting (ej: 100 llamadas por hora)
    
    Uso:
        @rate_limit(calls=50, period=60)  # 50 llamadas por minuto
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Debes autenticarte'
                }, status=401)
            
            # Crear clave única por usuario
            cache_key = f'rate_limit_{request.user.id}_{view_func.__name__}'
            request_count = cache.get(cache_key, 0)
            
            if request_count >= calls:
                logger.warning(f"Rate limit excedido para {request.user}")
                return JsonResponse({
                    'success': False,
                    'error': f'Límite de {calls} llamadas por {period} segundos excedido'
                }, status=429)
            
            # Incrementar y guardar en caché
            cache.set(cache_key, request_count + 1, period)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# 2. VALIDADORES PERSONALIZADOS
# ============================================================================

def validar_transicion_estado(estado_actual, nuevo_estado):
    """
    Valida si una transición de estado es permitida.
    
    Lógica de transiciones permitidas:
    - pendiente → en_proceso, cancelado
    - en_proceso → completado, pendiente, cancelado
    - completado → (ninguna, es estado final)
    - cancelado → pendiente
    
    Args:
        estado_actual (str): Estado actual de la tarea
        nuevo_estado (str): Estado al que se quiere mover
        
    Returns:
        tuple: (es_valida, mensaje_error)
    """
    
    transiciones_permitidas = {
        'pendiente': ['en_proceso', 'cancelado'],
        'en_proceso': ['completado', 'pendiente', 'cancelado'],
        'completado': [],  # Estado final, no permite transiciones
        'cancelado': ['pendiente'],  # Solo se puede reactivar
    }
    
    if estado_actual not in transiciones_permitidas:
        return False, f'Estado actual inválido: {estado_actual}'
    
    if nuevo_estado not in transiciones_permitidas[estado_actual]:
        estados_permitidos = ', '.join(transiciones_permitidas[estado_actual])
        return False, f'No se puede pasar de "{estado_actual}" a "{nuevo_estado}". Permitidos: {estados_permitidos}'
    
    return True, None


def validar_cambio_solo_si_no_pagada(tarea):
    """
    Valida que una tarea solo sea movida a 'completado' si está pagada.
    
    Args:
        tarea (TareaPlanificada): Instancia de tarea
        
    Returns:
        tuple: (es_valida, mensaje_error)
    """
    if tarea.estado != 'completado' and tarea.saldo_pendiente > 0:
        return True, None  # Permitir otros cambios aunque tenga deuda
    
    if tarea.estado == 'completado' and tarea.saldo_pendiente > 0:
        return False, f'No se puede completar: tiene ${tarea.saldo_pendiente:.2f} pendiente de pago'
    
    return True, None


# ============================================================================
# 3. CONFIGURACIÓN DE PERMISOS
# ============================================================================

def setup_permisos_kanban():
    """
    Crea los grupos de permisos necesarios para el Kanban.
    Ejecutar una sola vez: python manage.py shell < setup_permisos.py
    """
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from paneltareas.models import TareaPlanificada
    
    # Crear grupos
    grupo_visualizar, created = Group.objects.get_or_create(name='Kanban_Visualizar')
    grupo_editar, created = Group.objects.get_or_create(name='Kanban_Editar')
    grupo_admin, created = Group.objects.get_or_create(name='Kanban_Admin')
    
    # Obtener permisos
    content_type = ContentType.objects.get_for_model(TareaPlanificada)
    
    # Permisos para cada grupo
    permisos_visualizar = Permission.objects.filter(
        content_type=content_type,
        codename__in=['view_tareaplani ficada']
    )
    
    permisos_editar = Permission.objects.filter(
        content_type=content_type,
        codename__in=['view_tareaplani ficada', 'change_tareaplani ficada']
    )
    
    permisos_admin = Permission.objects.filter(content_type=content_type)
    
    # Asignar permisos
    grupo_visualizar.permissions.set(permisos_visualizar)
    grupo_editar.permissions.set(permisos_editar)
    grupo_admin.permissions.set(permisos_admin)
    
    print("✅ Permisos de Kanban configurados")


# ============================================================================
# 4. CACHING
# ============================================================================

def invalidar_cache_tareas():
    """Invalida el caché de tareas (llamar cuando cambia algo)"""
    cache_keys = [
        'tareas_kanban_all',
        'tareas_kanban_stats',
    ]
    cache.delete_many(cache_keys)
    logger.info("Cache de tareas invalidado")


def cache_tareas(timeout=300):
    """
    Decorador para cachear resultados de tareas por 5 minutos.
    Útil para endpoints de obtención que no cambian frecuentemente.
    
    Uso:
        @cache_tareas(timeout=600)  # 10 minutos
        def get_tareas_kanban(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Crear clave de caché basada en parámetros
            filtros = '|'.join(f"{k}={v}" for k, v in request.GET.items())
            cache_key = f'tareas_kanban_{filtros}' if filtros else 'tareas_kanban_all'
            
            # Intentar obtener del caché
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return JsonResponse(cached_data)
            
            # Si no está en caché, ejecutar vista
            response = view_func(request, *args, **kwargs)
            
            # Cachear respuesta
            try:
                data = response.json() if hasattr(response, 'json') else response
                cache.set(cache_key, data, timeout)
                logger.debug(f"Cache set: {cache_key} ({timeout}s)")
            except:
                pass  # Si no se puede cachear, continuar sin caché
            
            return response
        
        return wrapper
    return decorator


# ============================================================================
# 5. LOGGING AVANZADO
# ============================================================================

def log_evento_kanban(usuario, accion, tarea_id, detalles=''):
    """
    Registra eventos importantes del Kanban para auditoría.
    
    Args:
        usuario: Usuario que realiza la acción
        accion: Tipo de acción (move, view, filter, etc)
        tarea_id: ID de la tarea (si aplica)
        detalles: Información adicional
    """
    mensaje = f"[KANBAN] Usuario={usuario.username} | Accion={accion} | Tarea={tarea_id} | {detalles}"
    logger.info(mensaje)
    
    # Opcionalmente guardar en BD
    # from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
    # LogEntry.objects.create(...)


# ============================================================================
# 6. CONFIGURACIÓN SETTINGS.PY
# ============================================================================

"""
Agregar a tu settings.py:

# KANBAN CONFIGURATION
KANBAN_CONFIG = {
    # Caché
    'CACHE_TIMEOUT': 300,  # 5 minutos
    'ENABLE_CACHE': True,
    
    # Rate Limiting
    'RATE_LIMIT_ENABLED': True,
    'RATE_LIMIT_CALLS': 100,
    'RATE_LIMIT_PERIOD': 3600,  # 1 hora
    
    # Validaciones
    'VALIDAR_PAGO_ANTES_COMPLETAR': True,
    'VALIDAR_TRANSICIONES': True,
    'PERMITIR_CANCELACION_COMPLETADA': False,
    
    # Seguridad
    'REQUIRE_JEFE': True,
    'ENABLE_AUDIT_LOG': True,
    'AUDIT_LOG_FILE': 'logs/kanban_audit.log',
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'kanban_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/kanban.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'paneltareas.views_kanban': {
            'handlers': ['kanban_file'],
            'level': 'INFO',
        },
    },
}
"""

# ============================================================================
# 7. MIDDLEWARE PERSONALIZADO (Opcional)
# ============================================================================

class KanbanSecurityMiddleware:
    """
    Middleware que añade seguridad adicional al Kanban.
    
    Uso en settings.py:
        MIDDLEWARE = [
            ...
            'paneltareas.middleware.KanbanSecurityMiddleware',
        ]
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Procesar request
        response = self.get_response(request)
        
        # Procesar response
        if '/kanban/' in request.path:
            # Agregar headers de seguridad
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'
            response['X-XSS-Protection'] = '1; mode=block'
        
        return response


# ============================================================================
# 8. ESTADÍSTICAS Y MONITOREO
# ============================================================================

def obtener_estadisticas_kanban():
    """
    Obtiene estadísticas de uso del Kanban.
    
    Returns:
        dict: Información sobre uso y performance
    """
    from paneltareas.models import TareaPlanificada
    from django.utils import timezone
    from datetime import timedelta
    
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    
    stats = {
        'total_tareas': TareaPlanificada.objects.count(),
        'tareas_hoy': TareaPlanificada.objects.filter(
            fecha_entrega=hoy
        ).count(),
        'tareas_semana': TareaPlanificada.objects.filter(
            fecha_entrega__gte=hace_7_dias
        ).count(),
        'por_estado': {
            'pendiente': TareaPlanificada.objects.filter(estado='pendiente').count(),
            'en_proceso': TareaPlanificada.objects.filter(estado='en_proceso').count(),
            'completado': TareaPlanificada.objects.filter(estado='completado').count(),
            'cancelado': TareaPlanificada.objects.filter(estado='cancelado').count(),
        },
        'tareas_vencidas': TareaPlanificada.objects.filter(
            fecha_entrega__lt=hoy,
            estado__in=['pendiente', 'en_proceso']
        ).count(),
        'deuda_total': sum(
            t.saldo_pendiente for t in TareaPlanificada.objects.all()
        ),
    }
    
    return stats


# ============================================================================
# SCRIPT DE PRUEBA DE SEGURIDAD
# ============================================================================

def test_seguridad():
    """Script para probar la seguridad del Kanban"""
    print("=" * 60)
    print("PRUEBAS DE SEGURIDAD - KANBAN BOARD")
    print("=" * 60)
    
    # Test 1: Validar transiciones
    print("\n1️⃣  Probando validaciones de transición...")
    casos_prueba = [
        ('pendiente', 'en_proceso', True),
        ('pendiente', 'completado', False),
        ('en_proceso', 'completado', True),
        ('completado', 'pendiente', False),
        ('cancelado', 'pendiente', True),
    ]
    
    for actual, nuevo, esperado in casos_prueba:
        es_valida, error = validar_transicion_estado(actual, nuevo)
        resultado = "✅" if es_valida == esperado else "❌"
        print(f"  {resultado} {actual} → {nuevo}: {es_valida}")
    
    # Test 2: Obtener estadísticas
    print("\n2️⃣  Obtener estadísticas...")
    stats = obtener_estadisticas_kanban()
    print(f"  Total tareas: {stats['total_tareas']}")
    print(f"  Tareas vencidas: {stats['tareas_vencidas']}")
    print(f"  Deuda total: ${stats['deuda_total']:.2f}")
    
    print("\n✅ Pruebas completadas")


if __name__ == '__main__':
    test_seguridad()
