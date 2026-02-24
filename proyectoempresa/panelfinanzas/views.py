from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncMonth
from functools import wraps
from datetime import date, timedelta
from decimal import Decimal

from .models import Producto, CategoriaProducto, PerfilUsuario
from .forms import ProductoForm, CategoriaProductoForm, FiltroProductoForm


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
# VISTAS DE PRODUCTOS (SOLO JEFES)
# =============================================

@solo_jefes
def lista_productos(request):
    """Lista de todos los productos con filtros"""
    productos = Producto.objects.all()
    form_filtro = FiltroProductoForm(request.GET)
    
    # Aplicar filtros
    if form_filtro.is_valid():
        fecha_desde = form_filtro.cleaned_data.get('fecha_desde')
        fecha_hasta = form_filtro.cleaned_data.get('fecha_hasta')
        categoria = form_filtro.cleaned_data.get('categoria')
        
        if fecha_desde:
            productos = productos.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            productos = productos.filter(fecha__lte=fecha_hasta)
        if categoria:
            productos = productos.filter(categoria=categoria)
    
    # Calcular totales
    totales = productos.aggregate(
        total_costo=Sum('precio_costo'),
        total_venta=Sum('precio_venta'),
        total_cantidad=Sum('cantidad')
    )
    
    # Calcular ganancia total
    ganancia_total = Decimal('0')
    for producto in productos:
        ganancia_total += producto.ganancia_total
    
    context = {
        'productos': productos,
        'form_filtro': form_filtro,
        'totales': totales,
        'ganancia_total': ganancia_total,
    }
    return render(request, 'panelfinanzas/lista.html', context)


@solo_jefes
def crear_producto(request):
    """Crear un nuevo producto"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.creado_por = request.user
            producto.save()
            messages.success(request, 'Producto registrado correctamente.')
            return redirect('finanzas:lista')
    else:
        form = ProductoForm(initial={'fecha': date.today()})
    
    return render(request, 'panelfinanzas/crear.html', {'form': form})


@solo_jefes
def detalle_producto(request, pk):
    """Ver detalle de un producto"""
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'panelfinanzas/detalle.html', {'producto': producto})


@solo_jefes
def editar_producto(request, pk):
    """Editar un producto existente"""
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
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
# VISTAS DE REPORTES (SOLO JEFES)
# =============================================

@solo_jefes
def reporte_finanzas(request):
    """Reporte general de finanzas"""
    # Obtener rango de fechas (por defecto último mes)
    hoy = date.today()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        fecha_desde = date.fromisoformat(fecha_desde)
    else:
        fecha_desde = hoy.replace(day=1)
    
    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta)
    else:
        fecha_hasta = hoy
    
    # Filtrar productos por rango de fechas
    productos = Producto.objects.filter(fecha__gte=fecha_desde, fecha__lte=fecha_hasta)
    
    # Estadísticas generales
    total_productos = productos.count()
    total_cantidad = productos.aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Calcular totales financieros
    total_costos = Decimal('0')
    total_ventas = Decimal('0')
    total_ganancias = Decimal('0')
    
    for producto in productos:
        total_costos += producto.total_costo
        total_ventas += producto.total_venta
        total_ganancias += producto.ganancia_total
    
    # Porcentaje de ganancia promedio
    porcentaje_ganancia = 0
    if total_costos > 0:
        porcentaje_ganancia = ((total_ventas - total_costos) / total_costos) * 100
    
    # Productos por categoría
    por_categoria = productos.values('categoria__nombre').annotate(
        cantidad=Count('id'),
        total_ganancia=Sum('precio_venta') - Sum('precio_costo')
    ).order_by('-total_ganancia')
    
    # Top 5 productos más rentables
    top_productos = sorted(productos, key=lambda x: x.ganancia_total, reverse=True)[:5]
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_productos': total_productos,
        'total_cantidad': total_cantidad,
        'total_costos': total_costos,
        'total_ventas': total_ventas,
        'total_ganancias': total_ganancias,
        'porcentaje_ganancia': porcentaje_ganancia,
        'por_categoria': por_categoria,
        'top_productos': top_productos,
    }
    
    return render(request, 'panelfinanzas/reporte.html', context)


# =============================================
# VISTAS DE CATEGORÍAS (SOLO JEFES)
# =============================================

@solo_jefes
def lista_categorias(request):
    """Lista de categorías de productos"""
    categorias = CategoriaProducto.objects.annotate(
        num_productos=Count('productos')
    )
    return render(request, 'panelfinanzas/categorias/lista.html', {'categorias': categorias})


@solo_jefes
def crear_categoria(request):
    """Crear una nueva categoría"""
    if request.method == 'POST':
        form = CategoriaProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('finanzas:lista_categorias')
    else:
        form = CategoriaProductoForm()
    
    return render(request, 'panelfinanzas/categorias/crear.html', {'form': form})


@solo_jefes
def editar_categoria(request, pk):
    """Editar una categoría"""
    categoria = get_object_or_404(CategoriaProducto, pk=pk)
    
    if request.method == 'POST':
        form = CategoriaProductoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada correctamente.')
            return redirect('finanzas:lista_categorias')
    else:
        form = CategoriaProductoForm(instance=categoria)
    
    return render(request, 'panelfinanzas/categorias/editar.html', {
        'form': form, 
        'categoria': categoria
    })


@solo_jefes
def eliminar_categoria(request, pk):
    """Eliminar una categoría"""
    categoria = get_object_or_404(CategoriaProducto, pk=pk)
    
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada correctamente.')
        return redirect('finanzas:lista_categorias')
    
    return render(request, 'panelfinanzas/categorias/eliminar.html', {'categoria': categoria})
