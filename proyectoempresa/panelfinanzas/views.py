from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Sum, Avg, Count, F, DecimalField
from django.db.models.functions import TruncMonth
from functools import wraps
from datetime import date, timedelta
from decimal import Decimal

from .models import Producto, PerfilUsuario, Gasto
from .forms import ProductoForm, FiltroProductoForm, FiltroHistorialForm, GastoForm
from paneltareas.models import ProductoTarea


# =============================================
# DECORADORES PERSONALIZADOS
# =============================================

def solo_jefes(view_func):
    """Decorador que solo permite acceso a usuarios con rol de jefe"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder.')
            return redirect('finanzas:login')
        
        # Superusuarios siempre tienen acceso
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Verificar si tiene perfil y es jefe
        try:
            if not request.user.perfil.es_jefe:
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('home')
        except PerfilUsuario.DoesNotExist:
            messages.error(request, 'Tu usuario no tiene un perfil configurado.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# =============================================
# VISTAS DE AUTENTICACIÓN
# =============================================

def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            
            # Redirigir según el rol
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'panelfinanzas/login.html')


def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('finanzas:login')


# =============================================
# VISTAS DE PRODUCTOS / CATÁLOGO (SOLO JEFES)
# =============================================

@solo_jefes
def lista_productos(request):
    """Lista del catálogo de productos"""
    productos = Producto.objects.all()
    form_filtro = FiltroProductoForm(request.GET)
    
    # Aplicar filtros
    if form_filtro.is_valid():
        buscar = form_filtro.cleaned_data.get('buscar')
        
        if buscar:
            productos = productos.filter(nombre__icontains=buscar)
    
    # Producto Más Vendido
    mas_vendido = ProductoTarea.objects.filter(producto__isnull=False).values('producto_id', 'producto__nombre').annotate(total=Sum('cantidad')).order_by('-total').first()
    
    tareas_mas_vendido = []
    if mas_vendido and mas_vendido.get('producto_id'):
        tareas_mas_vendido = ProductoTarea.objects.filter(
            producto_id=mas_vendido['producto_id']
        ).select_related('tarea').order_by('-tarea__fecha_ingreso')
    
    # Ganancia total histórica de todos los productos vendidos
    ganancia_total_historica = sum(pt.ganancia_total for pt in ProductoTarea.objects.all())
    
    context = {
        'productos': productos,
        'form_filtro': form_filtro,
        'mas_vendido': mas_vendido,
        'tareas_mas_vendido': tareas_mas_vendido,
        'ganancia_total_historica': ganancia_total_historica,
    }
    return render(request, 'panelfinanzas/lista.html', context)


@solo_jefes
def crear_producto(request):
    """Crear un nuevo producto en el catálogo"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.creado_por = request.user
            producto.save()
            messages.success(request, 'Producto registrado correctamente.')
            return redirect('finanzas:lista')
    else:
        form = ProductoForm()
    
    return render(request, 'panelfinanzas/crear.html', {'form': form})


@solo_jefes
def detalle_producto(request, pk):
    """Ver detalle de un producto del catálogo"""
    producto = get_object_or_404(Producto, pk=pk)
    # Obtener historial de entregas de este producto
    entregas = ProductoTarea.objects.filter(producto=producto).select_related('tarea')
    return render(request, 'panelfinanzas/detalle.html', {
        'producto': producto,
        'entregas': entregas,
    })


@solo_jefes
def editar_producto(request, pk):
    """Editar un producto existente"""
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            # Actualizar precio_costo en todas las tareas que usan este producto
            ProductoTarea.objects.filter(
                producto=producto,
            ).update(precio_costo=producto.precio_costo)
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('finanzas:detalle', pk=pk)
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'panelfinanzas/editar.html', {'form': form, 'producto': producto})


@solo_jefes
def eliminar_producto(request, pk):
    """Eliminar un producto"""
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('finanzas:lista')
    
    return render(request, 'panelfinanzas/eliminar.html', {'producto': producto})


# =============================================
# VISTAS DE HISTORIAL DE ENTREGAS (SOLO JEFES)
# =============================================

@solo_jefes
def historial_entregas(request):
    """Historial de productos entregados con sus finanzas"""
    entregas = ProductoTarea.objects.all().select_related('tarea', 'producto')
    form_filtro = FiltroHistorialForm(request.GET)
    
    # Aplicar filtros
    if form_filtro.is_valid():
        fecha_desde = form_filtro.cleaned_data.get('fecha_desde')
        fecha_hasta = form_filtro.cleaned_data.get('fecha_hasta')
        
        if fecha_desde:
            entregas = entregas.filter(fecha_registro__date__gte=fecha_desde)
        if fecha_hasta:
            entregas = entregas.filter(fecha_registro__date__lte=fecha_hasta)
    
    # Calcular totales
    total_costo = Decimal('0')
    total_venta = Decimal('0')
    total_ganancia = Decimal('0')
    total_cantidad = 0
    
    for entrega in entregas:
        total_costo += entrega.total_costo
        total_venta += entrega.total_venta
        total_ganancia += entrega.ganancia_total
        total_cantidad += entrega.cantidad
    
    context = {
        'entregas': entregas,
        'form_filtro': form_filtro,
        'total_costo': total_costo,
        'total_venta': total_venta,
        'total_ganancia': total_ganancia,
        'total_cantidad': total_cantidad,
    }
    return render(request, 'panelfinanzas/historial.html', context)


# =============================================
# VISTAS DE REPORTES (SOLO JEFES)
# =============================================

@solo_jefes
def reporte_finanzas(request):
    """Reporte general de finanzas basado en entregas"""
    hoy = date.today()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        fecha_desde = date.fromisoformat(fecha_desde)
    else:
        # Por defecto muestra todo el año si no hay filtro activo
        fecha_desde = hoy.replace(month=1, day=1)
    
    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = hoy
    
    from paneltareas.models import TareaPlanificada

    # Filtrar entregas por rango de fechas
    entregas = ProductoTarea.objects.filter(
        fecha_registro__date__gte=fecha_desde,
        fecha_registro__date__lte=fecha_hasta
    ).select_related('producto', 'tarea')

    # Total cobrado: suma de monto_abonado de tareas con entregas en el período
    tareas_en_periodo = TareaPlanificada.objects.exclude(estado='cancelado').filter(
        fecha_ingreso__gte=fecha_desde,
        fecha_ingreso__lte=fecha_hasta
    )
    total_cobrado = sum(t.monto_abonado for t in tareas_en_periodo)
    total_facturado_periodo = sum(t.precio_total for t in tareas_en_periodo)
    saldo_pendiente_periodo = total_facturado_periodo - total_cobrado
    
    # Estadísticas generales
    total_entregas = entregas.count()
    total_cantidad = 0
    
    # Calcular totales financieros
    total_costos = Decimal('0')
    total_ventas = Decimal('0')
    total_ganancias = Decimal('0')
    
    for entrega in entregas:
        total_costos += entrega.total_costo
        total_ventas += entrega.total_venta
        total_ganancias += entrega.ganancia_total
        total_cantidad += entrega.cantidad
    
    # Porcentaje de ganancia promedio
    porcentaje_ganancia = 0
    if total_costos > 0:
        porcentaje_ganancia = ((total_ventas - total_costos) / total_costos) * 100
    
    # Top 5 productos más entregados
    prod_dict = {}
    for e in entregas:
        nombre = e.nombre_producto
        if nombre not in prod_dict:
            prod_dict[nombre] = {'nombre_producto': nombre, 'total_cant': 0, 'total_cos': Decimal('0'), 'total_gan': Decimal('0')}
        prod_dict[nombre]['total_cant'] += e.cantidad
        prod_dict[nombre]['total_cos'] += e.total_costo
        prod_dict[nombre]['total_gan'] += e.ganancia_total
    top_productos = sorted(prod_dict.values(), key=lambda x: x['total_cant'], reverse=True)[:5]
    
    # ==========================================
    # GASTOS EN EL PERÍODO
    # ==========================================
    gastos = Gasto.objects.filter(
        fecha__gte=fecha_desde,
        fecha__lte=fecha_hasta
    )
    
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    # Gastos por categoría
    gastos_por_categoria = gastos.values('categoria').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Mapear nombres de categorías
    cat_display = dict(Gasto.CATEGORIA_CHOICES)
    for g in gastos_por_categoria:
        g['categoria_display'] = cat_display.get(g['categoria'], g['categoria'])
    
    # Ganancia real = ventas - costos - gastos
    ganancia_real = total_ventas - total_costos - total_gastos
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_entregas': total_entregas,
        'total_cantidad': total_cantidad,
        'total_costos': total_costos,
        'total_ventas': total_ventas,
        'total_ganancias': total_ganancias,
        'porcentaje_ganancia': porcentaje_ganancia,
        'top_productos': top_productos,
        'total_gastos': total_gastos,
        'gastos_por_categoria': gastos_por_categoria,
        'ganancia_real': ganancia_real,
        'gastos_lista': gastos,
        'total_cobrado': total_cobrado,
        'total_facturado_periodo': total_facturado_periodo,
        'saldo_pendiente_periodo': saldo_pendiente_periodo,
    }
    
    return render(request, 'panelfinanzas/reporte.html', context)


# =============================================
# VISTAS DE GASTOS (SOLO JEFES)
# =============================================

@solo_jefes
def lista_gastos(request):
    """Lista de gastos del negocio"""
    gastos = Gasto.objects.all()
    
    # Filtros
    categoria_filtro = request.GET.get('categoria')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if categoria_filtro:
        gastos = gastos.filter(categoria=categoria_filtro)
    if fecha_desde:
        gastos = gastos.filter(fecha__gte=date.fromisoformat(fecha_desde))
    if fecha_hasta:
        gastos = gastos.filter(fecha__lte=date.fromisoformat(fecha_hasta))
    
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    context = {
        'gastos': gastos,
        'total_gastos': total_gastos,
        'categorias': Gasto.CATEGORIA_CHOICES,
    }
    return render(request, 'panelfinanzas/gastos/lista.html', context)


@solo_jefes
def crear_gasto(request):
    """Crear un nuevo gasto"""
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.creado_por = request.user
            gasto.save()
            messages.success(request, 'Gasto registrado correctamente.')
            return redirect('finanzas:lista_gastos')
    else:
        form = GastoForm(initial={'fecha': date.today()})
    
    return render(request, 'panelfinanzas/gastos/crear.html', {'form': form})


@solo_jefes
def editar_gasto(request, pk):
    """Editar un gasto existente"""
    gasto = get_object_or_404(Gasto, pk=pk)
    
    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto actualizado correctamente.')
            return redirect('finanzas:lista_gastos')
    else:
        form = GastoForm(instance=gasto)
    
    return render(request, 'panelfinanzas/gastos/editar.html', {'form': form, 'gasto': gasto})


@solo_jefes
def eliminar_gasto(request, pk):
    """Eliminar un gasto"""
    gasto = get_object_or_404(Gasto, pk=pk)
    
    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto eliminado correctamente.')
        return redirect('finanzas:lista_gastos')
    
    return render(request, 'panelfinanzas/gastos/eliminar.html', {'gasto': gasto})
