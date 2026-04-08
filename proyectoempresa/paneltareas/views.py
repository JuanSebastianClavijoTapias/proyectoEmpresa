from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date, timedelta
import calendar
import json
from .models import Cliente, TareaPlanificada, ImagenTarea, ProductoTarea
from .forms import TareaPlanificadaForm, TareaPlanificadaFormJefe, ClienteForm, ImagenTareaForm, ProductoTareaFormSet, AbonarForm
from panelfinanzas.models import Producto, PerfilUsuario


def es_jefe(user):
    """Verifica si el usuario es jefe o superusuario"""
    if user.is_superuser:
        return True
    try:
        return user.perfil.es_jefe
    except (PerfilUsuario.DoesNotExist, AttributeError):
        return False


# =============================================
# VISTAS DE AUTENTICACIÓN
# =============================================

def login_view(request):
    """Vista principal de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'login.html')


def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


# =============================================
# VISTAS PRINCIPALES
# =============================================

@login_required
def home(request):
    """Vista principal del dashboard"""
    # Si es trabajador, mostrar solo sus tareas asignadas
    es_trabajador_logueado = hasattr(request.user, 'trabajador')
    
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
        'es_trabajador': es_trabajador_logueado,
    }
    return render(request, 'home.html', context)


@login_required
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


@login_required
def crear_tarea(request):
    """Vista para crear una nueva tarea planificada con productos"""
    usuario_es_jefe = es_jefe(request.user)
    FormClass = TareaPlanificadaFormJefe if usuario_es_jefe else TareaPlanificadaForm
    
    if request.method == 'POST':
        form = FormClass(request.POST)
        formset = ProductoTareaFormSet(request.POST, prefix='productos')
        if form.is_valid() and formset.is_valid():
            tarea = form.save(commit=False)
            tarea.placa = ''
            tarea.save()
            formset.instance = tarea
            productos_tarea = formset.save(commit=False)
            for i, pt in enumerate(productos_tarea):
                form_data = formset.forms[i].cleaned_data
                nombre_input = form_data.get('nombre_producto_input', '').strip()
                precio_cobrado = form_data.get('precio_cobrado')
                
                if not nombre_input and not pt.producto:
                    continue
                
                if pt.producto:
                    pt.nombre_producto = pt.producto.nombre
                    pt.precio_costo = pt.producto.precio_costo
                    pt.precio_venta = precio_cobrado if precio_cobrado else pt.producto.precio_venta
                else:
                    pt.nombre_producto = nombre_input
                    pt.precio_costo = 0
                    pt.precio_venta = precio_cobrado if precio_cobrado else 0
                pt.ajuste_precio = 0
                pt.save()
            for obj in formset.deleted_objects:
                obj.delete()
            # Auto-set tarea.placa from product placas
            placas = tarea.productos_tarea.exclude(placa='').values_list('placa', flat=True).distinct()
            tarea.placa = ', '.join(placas)
            tarea.save(update_fields=['placa'])
            messages.success(request, 'Tarea creada exitosamente.')
            return redirect('tareas:lista')
    else:
        form = FormClass(initial={'fecha_ingreso': date.today()})
        formset = ProductoTareaFormSet(prefix='productos')
    
    # Preparar datos de productos para JavaScript (autocompletar)
    productos_json = json.dumps([
        {'id': p.id, 'nombre': p.nombre}
        for p in Producto.objects.all()
    ])
    
    # Preparar datos de clientes para autocompletar
    clientes_json = json.dumps([
        {'id': c.id, 'nombre': c.nombre, 'telefono': c.telefono}
        for c in Cliente.objects.all()
    ])
    
    # Placas existentes para autocompletar
    placas_json = json.dumps(list(
        ProductoTarea.objects.exclude(placa='').values_list('placa', flat=True).distinct()
    ))
    
    return render(request, 'paneltareas/crear.html', {
        'form': form,
        'formset': formset,
        'productos_json': productos_json,
        'clientes_json': clientes_json,
        'placas_json': placas_json,
        'es_jefe': usuario_es_jefe,
    })


@login_required
def editar_tarea(request, pk):
    """Vista para editar una tarea existente con productos"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    usuario_es_jefe = es_jefe(request.user)
    FormClass = TareaPlanificadaFormJefe if usuario_es_jefe else TareaPlanificadaForm
    
    if request.method == 'POST':
        form = FormClass(request.POST, instance=tarea)
        formset = ProductoTareaFormSet(request.POST, instance=tarea, prefix='productos')
        if form.is_valid() and formset.is_valid():
            form.save()
            productos_tarea = formset.save(commit=False)
            for i, pt in enumerate(productos_tarea):
                form_data = formset.forms[i].cleaned_data
                nombre_input = form_data.get('nombre_producto_input', '').strip()
                precio_cobrado = form_data.get('precio_cobrado')
                
                if not nombre_input and not pt.producto:
                    continue
                
                if pt.producto:
                    pt.nombre_producto = pt.producto.nombre
                    pt.precio_costo = pt.producto.precio_costo
                    pt.precio_venta = precio_cobrado if precio_cobrado else pt.producto.precio_venta
                else:
                    pt.nombre_producto = nombre_input
                    pt.precio_costo = 0
                    pt.precio_venta = precio_cobrado if precio_cobrado else 0
                pt.ajuste_precio = 0
                pt.save()
            for obj in formset.deleted_objects:
                obj.delete()
            # Auto-set tarea.placa from product placas
            placas = tarea.productos_tarea.exclude(placa='').values_list('placa', flat=True).distinct()
            tarea.placa = ', '.join(placas)
            tarea.save(update_fields=['placa'])
            messages.success(request, 'Tarea actualizada exitosamente.')
            return redirect('tareas:lista')
    else:
        form = FormClass(instance=tarea)
        formset = ProductoTareaFormSet(instance=tarea, prefix='productos')
    
    # Preparar datos de productos para JavaScript (autocompletar)
    productos_json = json.dumps([
        {'id': p.id, 'nombre': p.nombre}
        for p in Producto.objects.all()
    ])
    
    # Preparar datos de clientes para autocompletar
    clientes_json = json.dumps([
        {'id': c.id, 'nombre': c.nombre, 'telefono': c.telefono}
        for c in Cliente.objects.all()
    ])
    
    # Placas existentes para autocompletar
    placas_json = json.dumps(list(
        ProductoTarea.objects.exclude(placa='').values_list('placa', flat=True).distinct()
    ))
    
    return render(request, 'paneltareas/editar.html', {
        'form': form,
        'formset': formset,
        'tarea': tarea,
        'productos_json': productos_json,
        'clientes_json': clientes_json,
        'placas_json': placas_json,
        'es_jefe': usuario_es_jefe,
    })


@login_required
def eliminar_tarea(request, pk):
    """Vista para eliminar una tarea"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea eliminada exitosamente.')
        return redirect('tareas:lista')
    
    return render(request, 'paneltareas/eliminar.html', {'tarea': tarea})


@login_required
def detalle_tarea(request, pk):
    """Vista para ver el detalle de una tarea y subir imágenes"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    usuario_es_jefe = es_jefe(request.user)
    
    if request.method == 'POST':
        form_imagen = ImagenTareaForm(request.POST, request.FILES)
        if form_imagen.is_valid():
            imagen = form_imagen.save(commit=False)
            imagen.tarea = tarea
            imagen.save()
            messages.success(request, 'Imagen subida exitosamente.')
            return redirect('tareas:detalle', pk=pk)
        else:
            messages.error(request, 'Error al subir la imagen. Verifica que sea un archivo de imagen válido.')
    else:
        form_imagen = ImagenTareaForm()
    
    imagenes = tarea.imagenes.all()
    productos_tarea = tarea.productos_tarea.all()
    
    form_abonar = AbonarForm() if usuario_es_jefe else None

    return render(request, 'paneltareas/detalle.html', {
        'tarea': tarea,
        'form_imagen': form_imagen,
        'imagenes': imagenes,
        'productos_tarea': productos_tarea,
        'es_jefe': usuario_es_jefe,
        'form_abonar': form_abonar,
    })


@login_required
def abonar_tarea(request, pk):
    """Vista para abonar dinero adicional a una tarea (solo jefes)"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    if not es_jefe(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('tareas:detalle', pk=pk)

    if request.method == 'POST':
        form = AbonarForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data['monto']
            saldo = tarea.saldo_pendiente
            if monto > saldo:
                messages.warning(request, f'El monto ingresado (${monto:,.0f}) supera el saldo pendiente (${saldo:,.0f}). Se ajustó al saldo pendiente.')
                monto = saldo
            tarea.monto_abonado += monto
            tarea.save()
            messages.success(request, f'Se abonaron ${monto:,.0f} exitosamente. Nuevo saldo pendiente: ${tarea.saldo_pendiente:,.0f}')
        else:
            messages.error(request, 'Monto inválido. Ingresa un valor mayor a 0.')
    return redirect('tareas:detalle', pk=pk)


@login_required
def completar_pago_tarea(request, pk):
    """Vista para completar el pago total de una tarea (solo jefes)"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    if not es_jefe(request.user):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('tareas:detalle', pk=pk)

    if request.method == 'POST':
        if tarea.saldo_pendiente > 0:
            tarea.monto_abonado = tarea.precio_total
            tarea.save()
            messages.success(request, '¡Pago completado! El saldo pendiente ahora es $0.')
        else:
            messages.info(request, 'Esta tarea ya está completamente pagada.')
    return redirect('tareas:detalle', pk=pk)


@login_required
def eliminar_imagen(request, pk, imagen_pk):
    """Vista para eliminar una imagen de una tarea"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    imagen = get_object_or_404(ImagenTarea, pk=imagen_pk, tarea=tarea)
    
    if request.method == 'POST':
        # Eliminar el archivo físico
        if imagen.imagen:
            imagen.imagen.delete(save=False)
        imagen.delete()
        messages.success(request, 'Imagen eliminada exitosamente.')
        return redirect('tareas:detalle', pk=pk)
    
    return redirect('tareas:detalle', pk=pk)


@login_required
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
@login_required
def lista_clientes(request):
    """Vista para listar todos los clientes"""
    clientes = Cliente.objects.all()
    buscar = request.GET.get('buscar')
    
    if buscar:
        clientes = clientes.filter(nombre__icontains=buscar) | clientes.filter(telefono__icontains=buscar)
    
    return render(request, 'paneltareas/clientes/lista.html', {'clientes': clientes})


@login_required
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


@login_required
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


@login_required
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
