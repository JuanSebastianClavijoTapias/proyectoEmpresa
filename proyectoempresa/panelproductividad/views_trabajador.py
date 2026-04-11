from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from panelproductividad.models import Trabajador, RegistroProductividad
from datetime import date, timedelta


def login_trabajador(request):
    """Vista de login para trabajadores"""
    if request.user.is_authenticated:
        return redirect('trabajador:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar que sea un trabajador
            trabajador = Trabajador.objects.filter(usuario=user).first()
            if trabajador:
                login(request, user)
                return redirect('trabajador:dashboard')
            else:
                messages.error(request, 'Cuenta no asociada a un trabajador.')
        else:
            messages.error(request, 'Usuario o contraseña inválidos.')
    
    return render(request, 'trabajador/login.html')


@login_required(login_url='trabajador:login')
def dashboard_trabajador(request):
    """Dashboard del trabajador con resumen de su productividad"""
    try:
        trabajador = request.user.trabajador
    except Trabajador.DoesNotExist:
        messages.error(request, 'No estás asociado a un trabajador.')
        return redirect('trabajador:login')
    
    # Datos generales
    hoy = date.today()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    
    # Registros del trabajador
    registro_hoy = RegistroProductividad.objects.filter(trabajador=trabajador, fecha=hoy).first()
    registros_semana = RegistroProductividad.objects.filter(trabajador=trabajador, fecha__gte=hace_7_dias)
    registros_mes = RegistroProductividad.objects.filter(trabajador=trabajador, fecha__gte=hace_30_dias)
    
    contexto = {
        'trabajador': trabajador,
        'registro_hoy': registro_hoy,
        'registros_semana': registros_semana,
        'registros_mes': registros_mes,
        'total_hoy': registro_hoy.total_items if registro_hoy else 0,
        'total_semana': sum(r.total_items for r in registros_semana),
        'total_mes': sum(r.total_items for r in registros_mes),
    }
    
    return render(request, 'trabajador/dashboard.html', contexto)


@login_required(login_url='trabajador:login')
def mi_productividad(request):
    """Vista detallada de la productividad del trabajador"""
    try:
        trabajador = request.user.trabajador
    except Trabajador.DoesNotExist:
        messages.error(request, 'No estás asociado a un trabajador.')
        return redirect('trabajador:login')
    
    registros = RegistroProductividad.objects.filter(trabajador=trabajador).order_by('-fecha', '-hora_inicio')
    
    contexto = {
        'trabajador': trabajador,
        'registros': registros,
    }
    
    return render(request, 'trabajador/productividad.html', contexto)


@login_required(login_url='trabajador:login')
def registrar_productividad(request):
    """Vista para registrar productividad diaria"""
    try:
        trabajador = request.user.trabajador
    except Trabajador.DoesNotExist:
        messages.error(request, 'No estás asociado a un trabajador.')
        return redirect('trabajador:login')
    
    if request.method == 'POST':
        from django import forms
        from panelproductividad.models import RegistroProductividad
        
        try:
            fecha = request.POST.get('fecha', date.today())
            hora_inicio = request.POST.get('hora_inicio')
            hora_finalizacion = request.POST.get('hora_finalizacion')
            
            registro = RegistroProductividad(
                trabajador=trabajador,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_finalizacion=hora_finalizacion,
                cortado=int(request.POST.get('cortado', 0)),
                marcado_piezas=int(request.POST.get('marcado_piezas', 0)),
                costura=int(request.POST.get('costura', 0)),
                armado=int(request.POST.get('armado', 0)),
                instalacion=int(request.POST.get('instalacion', 0)),
                sillas_realizadas=int(request.POST.get('sillas_realizadas', 0)),
                tapizado_puertas=int(request.POST.get('tapizado_puertas', 0)),
                tapizado_techo=int(request.POST.get('tapizado_techo', 0)),
                observaciones=request.POST.get('observaciones', ''),
            )
            registro.save()
            messages.success(request, '✓ Registro de productividad guardado exitosamente')
            return redirect('trabajador:productividad')
        except Exception as e:
            messages.error(request, f'Error al guardar el registro: {str(e)}')
    
    return render(request, 'trabajador/registrar_productividad.html', {'trabajador': trabajador})


def logout_trabajador(request):
    """Logout para trabajadores"""
    logout(request)
    return redirect('trabajador:login')
