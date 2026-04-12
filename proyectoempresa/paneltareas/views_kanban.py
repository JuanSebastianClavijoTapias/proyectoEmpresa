"""
Vistas para el tablero Kanban de tareas.
Proporciona endpoints para obtener tareas agrupadas por estado
y actualizar el estado de tareas mediante drag-and-drop.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
import json
import logging

from .models import TareaPlanificada

logger = logging.getLogger(__name__)
PRODUCTION = not settings.DEBUG

# ============================================================================
# VISTAS PARA TABLERO KANBAN
# ============================================================================

@login_required
def kanban_board(request):
    """
    Renderiza el tablero Kanban con todas las tareas organizadas por estado.
    
    GET - Retorna el HTML del tablero Kanban
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP
        
    Returns:
        HttpResponse: Template del tablero Kanban
    """
    # Obtener estadísticas para el dashboard
    total_tareas = TareaPlanificada.objects.count()
    tareas_por_estado = (
        TareaPlanificada.objects
        .values('estado')
        .annotate(count=Count('id'))
    )
    
    # Convertir a diccionario para acceso fácil en template
    estado_counts = {item['estado']: item['count'] for item in tareas_por_estado}
    
    context = {
        'total_tareas': total_tareas,
        'estado_counts': estado_counts,
        'estados': [
            {'key': 'pendiente', 'label': 'Pendiente', 'color': '#f39c12'},
            {'key': 'en_proceso', 'label': 'En Proceso', 'color': '#3498db'},
            {'key': 'completado', 'label': 'Completado', 'color': '#2ecc71'},
            {'key': 'cancelado', 'label': 'Cancelado', 'color': '#e74c3c'},
        ]
    }
    
    return render(request, 'paneltareas/kanban.html', context)


@require_http_methods(["GET"])
@login_required
def get_tareas_kanban(request):
    """
    API endpoint que retorna todas las tareas agrupadas por estado.
    
    Parámetros opcionales (GET):
        - filtro_cliente: Filtrar por nombre de cliente
        - filtro_placa: Filtrar por placa del vehículo
        - filtro_prioridad: Filtrar por prioridad (baja, media, alta, urgente)
        - page: Número de página (default: 1)
        - items_per_page: Items por página (default: 50, opciones: 10, 25, 50, 100)
    
    Returns:
        JsonResponse: {
            'success': bool,
            'data': {
                'pendiente': [...],
                'en_proceso': [...],
                'completado': [...],
                'cancelado': [...]
            },
            'stats': {
                'total': int,
                'pendiente': int,
                'en_proceso': int,
                'completado': int,
                'cancelado': int
            },
            'pagination': {
                'pagina_actual': int,
                'total_paginas': int,
                'total_tareas': int,
                'items_por_pagina': int,
                'pagina_inicio': int,
                'pagina_fin': int
            }
        }
    """
    try:
        # Obtener parámetros de filtro
        filtro_cliente = request.GET.get('filtro_cliente', '').strip()
        filtro_placa = request.GET.get('filtro_placa', '').strip()
        filtro_prioridad = request.GET.get('filtro_prioridad', '').strip()
        
        # Parámetros de paginación
        pagina_num = request.GET.get('page', 1)
        items_por_pagina = request.GET.get('items_per_page', 50)
        
        # Validar items_por_pagina
        try:
            items_por_pagina = int(items_por_pagina)
            if items_por_pagina not in [10, 25, 50, 100]:
                items_por_pagina = 50
        except (ValueError, TypeError):
            items_por_pagina = 50
        
        # Base queryset
        tareas = TareaPlanificada.objects.all()
        
        # Aplicar filtros
        if filtro_cliente:
            tareas = tareas.filter(
                nombre_cliente__icontains=filtro_cliente
            )
        
        if filtro_placa:
            tareas = tareas.filter(
                placa__icontains=filtro_placa
            )
        
        if filtro_prioridad:
            tareas = tareas.filter(
                prioridad=filtro_prioridad
            )
        
        # Ordenar por fecha de entrega
        tareas = tareas.order_by('fecha_entrega')
        
        # Paginación
        paginator = Paginator(tareas, items_por_pagina)
        try:
            pagina = paginator.page(pagina_num)
        except PageNotAnInteger:
            pagina = paginator.page(1)
        except EmptyPage:
            pagina = paginator.page(paginator.num_pages)
        
        # Calcular indices para el rango mostrado
        total_tareas = paginator.count
        pagina_actual = pagina.number
        total_paginas = paginator.num_pages
        pagina_inicio = (pagina_actual - 1) * items_por_pagina + 1
        pagina_fin = min(pagina_actual * items_por_pagina, total_tareas)
        
        # Agrupar tareas por estado (solo las de la página actual)
        tareas_por_estado = {
            'pendiente': [],
            'en_proceso': [],
            'completado': [],
            'cancelado': []
        }
        
        stats = {
            'total': total_tareas,
            'pendiente': 0,
            'en_proceso': 0,
            'completado': 0,
            'cancelado': 0
        }
        
        # Serializar tareas de la página actual
        for tarea in pagina.object_list:
            tarea_data = serializar_tarea_kanban(tarea)
            estado = tarea.estado
            
            if estado in tareas_por_estado:
                tareas_por_estado[estado].append(tarea_data)
        
        # Calcular estadísticas totales (no solo de la página)
        all_tareas_stats = TareaPlanificada.objects.all()
        
        # Aplicar mismos filtros para estadísticas
        if filtro_cliente:
            all_tareas_stats = all_tareas_stats.filter(
                nombre_cliente__icontains=filtro_cliente
            )
        if filtro_placa:
            all_tareas_stats = all_tareas_stats.filter(
                placa__icontains=filtro_placa
            )
        if filtro_prioridad:
            all_tareas_stats = all_tareas_stats.filter(
                prioridad=filtro_prioridad
            )
        
        # Contar por estado
        for tarea in all_tareas_stats:
            stats[tarea.estado] += 1
        
        return JsonResponse({
            'success': True,
            'data': tareas_por_estado,
            'stats': stats,
            'pagination': {
                'pagina_actual': pagina_actual,
                'total_paginas': total_paginas,
                'total_tareas': total_tareas,
                'items_por_pagina': items_por_pagina,
                'pagina_inicio': pagina_inicio,
                'pagina_fin': pagina_fin
            }
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"Error en get_tareas_kanban: {error_msg}\n{error_traceback}")
        return JsonResponse({
            'success': False,
            'error': error_msg,
            'traceback': error_traceback if not PRODUCTION else 'Error'
        }, status=500)


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def actualizar_estado_tarea(request, tarea_id):
    """
    API endpoint para cambiar el estado de una tarea (drag-and-drop).
    
    Body (JSON):
        {
            'nuevo_estado': 'en_proceso|completado|pendiente|cancelado'
        }
    
    Returns:
        JsonResponse: {
            'success': bool,
            'message': str,
            'tarea': {...} (si success=True)
        }
    """
    try:
        # Obtener tarea
        tarea = get_object_or_404(TareaPlanificada, id=tarea_id)
        
        # Parsear JSON del body
        try:
            body = json.loads(request.body)
            nuevo_estado = body.get('nuevo_estado', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido en el body'
            }, status=400)
        
        # Validar nuevo estado
        estados_validos = ['pendiente', 'en_proceso', 'completado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'
            }, status=400)
        
        # Validar transiciones de estado (opcional - ajusta según tu lógica)
        estado_original = tarea.estado
        
        # Actualizar estado
        tarea.estado = nuevo_estado
        tarea.save()
        
        logger.info(
            f"Tarea #{tarea.id} movida de '{estado_original}' a '{nuevo_estado}' "
            f"por usuario {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Tarea actualizada a estado: {nuevo_estado}',
            'tarea': serializar_tarea_kanban(tarea)
        })
        
    except TareaPlanificada.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Tarea con ID {tarea_id} no encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en actualizar_estado_tarea: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def reordenar_tareas(request):
    """
    API endpoint para reordenar tareas dentro del mismo estado.
    Útil si implementas persistencia de orden personalizado.
    
    Body (JSON):
        {
            'tareas': [
                {'id': 1, 'estado': 'pendiente', 'orden': 1},
                {'id': 2, 'estado': 'pendiente', 'orden': 2},
                ...
            ]
        }
    
    Returns:
        JsonResponse: {'success': bool, 'message': str}
    """
    try:
        body = json.loads(request.body)
        tareas_data = body.get('tareas', [])
        
        for item in tareas_data:
            tarea_id = item.get('id')
            nuevo_estado = item.get('estado')
            
            tarea = get_object_or_404(TareaPlanificada, id=tarea_id)
            
            # Si cambió el estado, actualizarlo
            if tarea.estado != nuevo_estado:
                tarea.estado = nuevo_estado
                tarea.save()
        
        logger.info(
            f"Reorder de {len(tareas_data)} tareas realizado "
            f"por usuario {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{len(tareas_data)} tareas reordenadas'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Error en reordenar_tareas: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# FUNCIONES AUXILIARES DE SERIALIZACIÓN
# ============================================================================

def serializar_tarea_kanban(tarea):
    """
    Serializa una tarea para mostrar en el tablero Kanban.
    
    Args:
        tarea (TareaPlanificada): Instancia de la tarea
        
    Returns:
        dict: Datos serializados de la tarea
    """
    try:
        # Calcular colores de prioridad
        colores_prioridad = {
            'baja': '#95a5a6',
            'media': '#f39c12',
            'alta': '#e67e22',
            'urgente': '#e74c3c'
        }
        
        # Información de urgencia
        dias_restantes = tarea.dias_restantes
        urgencia_visual = 'normal'
        
        if dias_restantes < 0:
            urgencia_visual = 'vencida'
        elif dias_restantes == 0:
            urgencia_visual = 'hoy'
        elif dias_restantes <= 3:
            urgencia_visual = 'proxima'
        
        # Procesar descripción con seguridad
        descripcion = ''
        if tarea.descripcion_trabajo:
            descripcion = tarea.descripcion_trabajo[:50]
            if len(tarea.descripcion_trabajo) > 50:
                descripcion += '...'
        
        # Procesar valores monetarios con seguridad
        precio_total = float(tarea.precio_total or 0)
        monto_abonado = float(tarea.monto_abonado or 0)
        saldo_pendiente = float(tarea.saldo_pendiente or 0)
        
        # Calcular porcentaje de pago
        if precio_total > 0:
            porcentaje_pago = int((monto_abonado / precio_total) * 100)
        else:
            porcentaje_pago = 0
        
        return {
            'id': tarea.id,
            'cliente': tarea.nombre_cliente or 'Sin cliente',
            'placa': tarea.placa or 'N/A',
            'descripcion': descripcion or 'Sin descripción',
            'fecha_entrega': tarea.fecha_entrega.strftime('%d/%m/%Y') if tarea.fecha_entrega else 'Sin fecha',
            'dias_restantes': dias_restantes,
            'urgencia_visual': urgencia_visual,
            'prioridad': tarea.prioridad,
            'color_prioridad': colores_prioridad.get(tarea.prioridad, '#95a5a6'),
            'estado': tarea.estado,
            'saldo_pendiente': saldo_pendiente,
            'precio_total': precio_total,
            'monto_abonado': monto_abonado,
            'porcentaje_pago': porcentaje_pago
        }
    
    except Exception as e:
        logger.error(f"Error serializando tarea {tarea.id}: {str(e)}")
        raise
