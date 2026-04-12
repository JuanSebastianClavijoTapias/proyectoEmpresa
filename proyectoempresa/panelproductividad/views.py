from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from datetime import date, timedelta
from .models import Trabajador, RegistroProductividad
from .forms import RegistroProductividadForm, RegistroProductividadTrabajadorForm, TrabajadorForm


@login_required
def lista_productividad(request):
    """Vista para listar todos los registros de productividad"""
    registros = RegistroProductividad.objects.all()
    
    # Si es trabajador, solo ver sus propios registros
    if hasattr(request.user, 'trabajador'):
        registros = registros.filter(trabajador=request.user.trabajador)
    
    # Filtros
    fecha_filtro = request.GET.get('fecha')
    trabajador_filtro = request.GET.get('trabajador')
    
    if fecha_filtro:
        registros = registros.filter(fecha=fecha_filtro)
    if trabajador_filtro and not hasattr(request.user, 'trabajador'):
        registros = registros.filter(trabajador_id=trabajador_filtro)
    
    # Estadísticas del día
    hoy = date.today()
    registros_hoy = RegistroProductividad.objects.filter(fecha=hoy)
    if hasattr(request.user, 'trabajador'):
        registros_hoy = registros_hoy.filter(trabajador=request.user.trabajador)
    stats_hoy = registros_hoy.aggregate(
        cortado=Sum('cortado'),
        marcado=Sum('marcado_piezas'),
        costura=Sum('costura'),
        sillas=Sum('sillas_realizadas')
    )
    
    trabajadores = Trabajador.objects.filter(activo=True)
    
    context = {
        'registros': registros,
        'trabajadores': trabajadores,
        'stats_hoy': stats_hoy,
    }
    return render(request, 'panelproductividad/lista.html', context)


@login_required
def crear_productividad(request):
    """Vista para crear un nuevo registro de productividad"""
    # Verificar si el usuario actual es un trabajador
    es_trabajador = hasattr(request.user, 'trabajador')
    trabajador = request.user.trabajador if es_trabajador else None
    
    if request.method == 'POST':
        if es_trabajador:
            form = RegistroProductividadTrabajadorForm(request.POST)
            if form.is_valid():
                # Asignar automáticamente el trabajador logueado
                registro = form.save(commit=False)
                registro.trabajador = trabajador
                registro.save()
                messages.success(request, f'✓ Registro de productividad guardado en tu cuenta ({trabajador.nombre})')
                return redirect('productividad:lista')
        else:
            form = RegistroProductividadForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Registro de productividad creado exitosamente.')
                return redirect('productividad:lista')
    else:
        if es_trabajador:
            form = RegistroProductividadTrabajadorForm(initial={'fecha': date.today()})
        else:
            form = RegistroProductividadForm(initial={'fecha': date.today()})
    
    return render(request, 'panelproductividad/crear.html', {
        'form': form,
        'es_trabajador': es_trabajador,
        'trabajador': trabajador
    })


@login_required
def editar_productividad(request, pk):
    """Vista para editar un registro de productividad existente"""
    registro = get_object_or_404(RegistroProductividad, pk=pk)
    
    if request.method == 'POST':
        form = RegistroProductividadForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro actualizado exitosamente.')
            return redirect('productividad:lista')
    else:
        form = RegistroProductividadForm(instance=registro)
    
    return render(request, 'panelproductividad/editar.html', {'form': form, 'registro': registro})


@login_required
def eliminar_productividad(request, pk):
    """Vista para eliminar un registro de productividad"""
    registro = get_object_or_404(RegistroProductividad, pk=pk)
    
    if request.method == 'POST':
        registro.delete()
        messages.success(request, 'Registro eliminado exitosamente.')
        return redirect('productividad:lista')
    
    return render(request, 'panelproductividad/eliminar.html', {'registro': registro})


@login_required
def detalle_productividad(request, pk):
    """Vista para ver el detalle de un registro"""
    registro = get_object_or_404(RegistroProductividad, pk=pk)
    return render(request, 'panelproductividad/detalle.html', {'registro': registro})


# Vistas de Trabajadores
@login_required
def lista_trabajadores(request):
    """Vista para listar todos los trabajadores"""
    trabajadores = Trabajador.objects.all()
    
    # Calcular estadísticas para cada trabajador
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    for trabajador in trabajadores:
        # Estadísticas del día
        registros_hoy = trabajador.registros.filter(fecha=hoy)
        trabajador.stats_hoy = registros_hoy.aggregate(
            cortado=Sum('cortado'),
            marcado=Sum('marcado_piezas'),
            costura=Sum('costura'),
            armado=Sum('armado'),
            instalacion=Sum('instalacion'),
            sillas=Sum('sillas_realizadas'),
            puertas=Sum('tapizado_puertas'),
            techo=Sum('tapizado_techo')
        )
        
        # Total del mes
        registros_mes = trabajador.registros.filter(fecha__gte=inicio_mes)
        stats_mes = registros_mes.aggregate(
            total_cortado=Sum('cortado'),
            total_sillas=Sum('sillas_realizadas')
        )
        trabajador.total_cortado_mes = stats_mes['total_cortado'] or 0
        trabajador.total_sillas_mes = stats_mes['total_sillas'] or 0
    
    return render(request, 'panelproductividad/trabajadores/lista.html', {'trabajadores': trabajadores})


@login_required
def detalle_trabajador(request, pk):
    """Vista para ver el detalle y estadísticas de un trabajador"""
    trabajador = get_object_or_404(Trabajador, pk=pk)
    
    # Filtrar por fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    registros = trabajador.registros.all()
    
    if fecha_inicio:
        registros = registros.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha__lte=fecha_fin)
    
    # Estadísticas totales
    stats = registros.aggregate(
        total_cortado=Sum('cortado'),
        total_marcado=Sum('marcado_piezas'),
        total_costura=Sum('costura'),
        total_armado=Sum('armado'),
        total_instalacion=Sum('instalacion'),
        total_sillas=Sum('sillas_realizadas'),
        total_puertas=Sum('tapizado_puertas'),
        total_techo=Sum('tapizado_techo')
    )
    
    context = {
        'trabajador': trabajador,
        'registros': registros[:20],  # Últimos 20 registros
        'stats': stats,
    }
    return render(request, 'panelproductividad/trabajadores/detalle.html', context)


@login_required
def crear_trabajador(request):
    """Vista para crear un nuevo trabajador"""
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            trabajador = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if username and password:
                usuario = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=trabajador.nombre
                )
                # El PerfilUsuario se crea automáticamente con rol='trabajador'
                trabajador.usuario = usuario
            trabajador.save()
            messages.success(request, 'Trabajador creado exitosamente.')
            return redirect('productividad:lista_trabajadores')
    else:
        form = TrabajadorForm()
    
    return render(request, 'panelproductividad/trabajadores/crear.html', {'form': form})


@login_required
def editar_trabajador(request, pk):
    """Vista para editar un trabajador"""
    trabajador = get_object_or_404(Trabajador, pk=pk)
    
    if request.method == 'POST':
        form = TrabajadorForm(request.POST, instance=trabajador)
        if form.is_valid():
            trabajador = form.save(commit=False)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if username:
                if trabajador.usuario:
                    trabajador.usuario.username = username
                    if password:
                        trabajador.usuario.set_password(password)
                    trabajador.usuario.save()
                elif password:
                    usuario = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=trabajador.nombre
                    )
                    trabajador.usuario = usuario
            trabajador.save()
            messages.success(request, 'Trabajador actualizado exitosamente.')
            return redirect('productividad:lista_trabajadores')
    else:
        form = TrabajadorForm(instance=trabajador)
    
    return render(request, 'panelproductividad/trabajadores/editar.html', {'form': form, 'trabajador': trabajador})
