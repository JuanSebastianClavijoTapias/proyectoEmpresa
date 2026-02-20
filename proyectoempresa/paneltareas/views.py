from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date, timedelta
import calendar
from .models import Cliente, TareaPlanificada
from .forms import TareaPlanificadaForm, ClienteForm


def home(request):
    """Vista principal del dashboard"""
    # Estadísticas generales
    tareas_pendientes = TareaPlanificada.objects.filter(estado='pendiente').count()
    tareas_en_proceso = TareaPlanificada.objects.filter(estado='en_proceso').count()
    tareas_completadas = TareaPlanificada.objects.filter(estado='completado').count()
    total_clientes = Cliente.objects.count()
    
    # Tareas próximas a entregar (próximos 7 días)
    hoy = date.today()
    proxima_semana = hoy + __import__('datetime').timedelta(days=7)
    tareas_proximas = TareaPlanificada.objects.filter(
        estado__in=['pendiente', 'en_proceso'],
        fecha_entrega__lte=proxima_semana
    ).order_by('fecha_entrega')[:5]
    
    # Tareas urgentes (vencidas o por vencer hoy)
    tareas_urgentes = TareaPlanificada.objects.filter(
        estado__in=['pendiente', 'en_proceso'],
        fecha_entrega__lte=hoy
    ).count()
    
    context = {
        'tareas_pendientes': tareas_pendientes,
        'tareas_en_proceso': tareas_en_proceso,
        'tareas_completadas': tareas_completadas,
        'total_clientes': total_clientes,
        'tareas_proximas': tareas_proximas,
        'tareas_urgentes': tareas_urgentes,
    }
    return render(request, 'home.html', context)


def lista_tareas(request):
    """Vista para listar todas las tareas planificadas"""
    tareas = TareaPlanificada.objects.all()
    
    # Filtros
    estado_filtro = request.GET.get('estado')
    prioridad_filtro = request.GET.get('prioridad')
    placa_filtro = request.GET.get('placa')
    
    if estado_filtro:
        tareas = tareas.filter(estado=estado_filtro)
    if prioridad_filtro:
        tareas = tareas.filter(prioridad=prioridad_filtro)
    if placa_filtro:
        tareas = tareas.filter(placa__icontains=placa_filtro)
    
    context = {
        'tareas': tareas,
        'estados': TareaPlanificada.ESTADO_CHOICES,
        'prioridades': TareaPlanificada.PRIORIDAD_CHOICES,
    }
    return render(request, 'paneltareas/lista.html', context)


def crear_tarea(request):
    """Vista para crear una nueva tarea planificada"""
    if request.method == 'POST':
        form = TareaPlanificadaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarea creada exitosamente.')
            return redirect('tareas:lista')
    else:
        form = TareaPlanificadaForm(initial={'fecha_ingreso': date.today()})
    
    return render(request, 'paneltareas/crear.html', {'form': form})


def editar_tarea(request, pk):
    """Vista para editar una tarea existente"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    
    if request.method == 'POST':
        form = TareaPlanificadaForm(request.POST, instance=tarea)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarea actualizada exitosamente.')
            return redirect('tareas:lista')
    else:
        form = TareaPlanificadaForm(instance=tarea)
    
    return render(request, 'paneltareas/editar.html', {'form': form, 'tarea': tarea})


def eliminar_tarea(request, pk):
    """Vista para eliminar una tarea"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea eliminada exitosamente.')
        return redirect('tareas:lista')
    
    return render(request, 'paneltareas/eliminar.html', {'tarea': tarea})


def detalle_tarea(request, pk):
    """Vista para ver el detalle de una tarea"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    return render(request, 'paneltareas/detalle.html', {'tarea': tarea})


def cambiar_estado_tarea(request, pk, estado):
    """Vista para cambiar rápidamente el estado de una tarea"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    estados_validos = dict(TareaPlanificada.ESTADO_CHOICES).keys()
    
    if estado in estados_validos:
        tarea.estado = estado
        tarea.save()
        messages.success(request, f'Estado cambiado a {tarea.get_estado_display()}.')
    else:
        messages.error(request, 'Estado no válido.')
    
    return redirect('tareas:lista')


# Vistas para Clientes
def lista_clientes(request):
    """Vista para listar todos los clientes"""
    clientes = Cliente.objects.all()
    buscar = request.GET.get('buscar')
    
    if buscar:
        clientes = clientes.filter(nombre__icontains=buscar) | clientes.filter(telefono__icontains=buscar)
    
    return render(request, 'paneltareas/clientes/lista.html', {'clientes': clientes})


def crear_cliente(request):
    """Vista para crear un nuevo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('tareas:lista_clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'paneltareas/clientes/crear.html', {'form': form})


def editar_cliente(request, pk):
    """Vista para editar un cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('tareas:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'paneltareas/clientes/editar.html', {'form': form, 'cliente': cliente})


def calendario_tareas(request):
    """Vista de calendario para ver las fechas de entrega"""
    # Obtener mes y año de los parámetros o usar el actual
    hoy = date.today()
    año = int(request.GET.get('año', hoy.year))
    mes = int(request.GET.get('mes', hoy.month))
    
    # Validar mes
    if mes < 1:
        mes = 12
        año -= 1
    elif mes > 12:
        mes = 1
        año += 1
    
    # Crear calendario
    cal = calendar.Calendar(firstweekday=0)  # Lunes como primer día
    dias_mes = cal.monthdayscalendar(año, mes)
    
    # Obtener tareas del mes
    primer_dia = date(año, mes, 1)
    if mes == 12:
        ultimo_dia = date(año + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = date(año, mes + 1, 1) - timedelta(days=1)
    
    tareas_mes = TareaPlanificada.objects.filter(
        fecha_entrega__gte=primer_dia,
        fecha_entrega__lte=ultimo_dia
    ).exclude(estado__in=['completado', 'cancelado'])
    
    # Organizar tareas por día
    tareas_por_dia = {}
    for tarea in tareas_mes:
        dia = tarea.fecha_entrega.day
        if dia not in tareas_por_dia:
            tareas_por_dia[dia] = []
        tareas_por_dia[dia].append(tarea)
    
    # Nombres de los meses en español
    MESES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Crear datos para el template
    semanas = []
    for semana in dias_mes:
        dias_semana = []
        for dia in semana:
            if dia == 0:
                dias_semana.append({'dia': None, 'tareas': [], 'es_hoy': False, 'pasado': False})
            else:
                fecha_dia = date(año, mes, dia)
                es_hoy = fecha_dia == hoy
                es_pasado = fecha_dia < hoy
                dias_semana.append({
                    'dia': dia,
                    'tareas': tareas_por_dia.get(dia, []),
                    'es_hoy': es_hoy,
                    'pasado': es_pasado,
                    'fecha': fecha_dia
                })
        semanas.append(dias_semana)
    
    # Mes anterior y siguiente
    if mes == 1:
        mes_anterior = {'mes': 12, 'año': año - 1}
    else:
        mes_anterior = {'mes': mes - 1, 'año': año}
    
    if mes == 12:
        mes_siguiente = {'mes': 1, 'año': año + 1}
    else:
        mes_siguiente = {'mes': mes + 1, 'año': año}
    
    context = {
        'semanas': semanas,
        'mes_actual': mes,
        'año_actual': año,
        'nombre_mes': MESES[mes],
        'mes_anterior': mes_anterior,
        'mes_siguiente': mes_siguiente,
        'hoy': hoy,
        'dias_semana': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
    }
    
    return render(request, 'paneltareas/calendario.html', context)
