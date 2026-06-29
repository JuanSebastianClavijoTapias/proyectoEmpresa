from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import calendar
import json
import unicodedata
from .models import Cliente, TareaPlanificada, ImagenTarea, ProductoTarea, NotaTrabajo, _optimizar_imagen_bytes
from .forms import TareaPlanificadaForm, TareaPlanificadaFormJefe, ClienteForm, ImagenTareaForm, ProductoTareaFormSet, ProductoTareaFormSetEdit, AbonarForm, NotaTrabajoForm
from panelfinanzas.models import Producto, PerfilUsuario
from core.permissions import require_not_trabajador


def es_jefe(user):
    """Verifica si el usuario es jefe o superusuario"""
    if user.is_superuser:
        return True
    try:
        return user.perfil.es_jefe
    except (PerfilUsuario.DoesNotExist, AttributeError):
        return False


def guardar_imagenes_tarea(tarea, archivos, descripcion=''):
    """Valida y guarda imágenes asociadas a una tarea."""
    imagenes_pendientes = []

    for archivo in archivos:
        if not getattr(archivo, 'name', ''):
            continue

        imagen = ImagenTarea(
            tarea=tarea,
            imagen=archivo,
            descripcion=descripcion,
        )
        imagen.full_clean()
        imagenes_pendientes.append(imagen)

    for imagen in imagenes_pendientes:
        imagen.save()

    return len(imagenes_pendientes)


def guardar_imagenes_producto(producto_tarea, archivos, descripcion=''):
    """Valida y guarda imágenes asociadas a un producto dentro de una tarea."""
    imagenes_pendientes = []

    for archivo in archivos:
        if not getattr(archivo, 'name', ''):
            continue

        imagen = ImagenTarea(
            tarea=producto_tarea.tarea,
            producto_tarea=producto_tarea,
            imagen=archivo,
            descripcion=descripcion,
        )
        imagen.full_clean()
        imagenes_pendientes.append(imagen)

    for imagen in imagenes_pendientes:
        imagen.save()

    return len(imagenes_pendientes)


def obtener_mensajes_validacion(error):
    mensajes = []
    if hasattr(error, 'message_dict'):
        for errores in error.message_dict.values():
            mensajes.extend(errores)
    else:
        mensajes.extend(error.messages)
    return mensajes


def validar_imagenes_por_producto(formset, files):
    """Evita adjuntar imágenes en filas donde no se indicó producto."""
    es_valido = True

    for form_producto in formset.forms:
        cleaned_data = getattr(form_producto, 'cleaned_data', None)
        if not cleaned_data or cleaned_data.get('DELETE'):
            continue

        archivos = files.getlist(f'{form_producto.prefix}-imagenes')
        if not archivos:
            continue

        nombre_input = (cleaned_data.get('nombre_producto_input') or '').strip()
        producto = cleaned_data.get('producto')

        if nombre_input or producto:
            continue

        form_producto.add_error(
            'nombre_producto_input',
            'Debe seleccionar o escribir un producto antes de adjuntar imágenes.',
        )
        es_valido = False

    return es_valido


def guardar_productos_tarea(formset, tarea, usuario, files):
    """Guarda los productos del formset y sus imágenes asociadas."""
    total_imagenes = 0

    for form_producto in formset.forms:
        cleaned_data = getattr(form_producto, 'cleaned_data', None)
        if not cleaned_data or cleaned_data.get('DELETE'):
            continue

        producto_tarea = form_producto.save(commit=False)
        nombre_input = (cleaned_data.get('nombre_producto_input') or '').strip()
        precio_cobrado = cleaned_data.get('precio_cobrado')

        if not nombre_input and not producto_tarea.producto:
            continue

        if producto_tarea.producto:
            producto_tarea.nombre_producto = producto_tarea.producto.nombre
            producto_tarea.precio_costo = producto_tarea.producto.precio_costo
            producto_tarea.precio_venta = (
                precio_cobrado if precio_cobrado is not None else producto_tarea.producto.precio_venta
            )
        else:
            nuevo_producto, created = Producto.objects.get_or_create(
                nombre=nombre_input,
                defaults={
                    'precio_costo': 0,
                    'precio_venta': precio_cobrado or 0,
                    'creado_por': usuario,
                }
            )
            producto_tarea.producto = nuevo_producto
            producto_tarea.nombre_producto = nombre_input
            producto_tarea.precio_costo = nuevo_producto.precio_costo
            producto_tarea.precio_venta = (
                precio_cobrado if precio_cobrado is not None else nuevo_producto.precio_venta
            )

        producto_tarea.tarea = tarea
        producto_tarea.ajuste_precio = 0
        producto_tarea.save()

        total_imagenes += guardar_imagenes_producto(
            producto_tarea,
            files.getlist(f'{form_producto.prefix}-imagenes')
        )

    for form_eliminado in formset.deleted_forms:
        if form_eliminado.instance.pk:
            form_eliminado.instance.delete()

    placas = tarea.productos_tarea.exclude(placa='').values_list('placa', flat=True).distinct()
    tarea.placa = ', '.join(placas)
    tarea.save(update_fields=['placa'])

    return total_imagenes


def construir_clientes_formulario(mostrar_saldos=True):
    """Construye la lista de clientes para el selector y autocompletado, incluyendo saldos pendientes (solo si mostrar_saldos=True)."""
    clientes_map = {}

    def clave_cliente(nombre, telefono):
        return ((nombre or '').strip().lower(), (telefono or '').strip())

    for cliente in Cliente.objects.all().order_by('nombre', 'telefono'):
        nombre = (cliente.nombre or '').strip()
        telefono = (cliente.telefono or '').strip()
        if not nombre:
            continue

        clave = clave_cliente(nombre, telefono)
        clientes_map.setdefault(clave, {
            'selector_value': f'cliente:{cliente.pk}',
            'id': cliente.pk,
            'nombre': nombre,
            'telefono': telefono,
            'saldo_pendiente': Decimal('0'),
            'tiene_saldo': False,
        })

    if mostrar_saldos:
        tareas_con_cliente = (
            TareaPlanificada.objects
            .prefetch_related('productos_tarea')
            .exclude(nombre_cliente__isnull=True)
            .exclude(nombre_cliente='')
        )

        for tarea in tareas_con_cliente:
            saldo_pendiente = tarea.saldo_pendiente
            nombre = (tarea.nombre_cliente or '').strip()
            telefono = (tarea.telefono_cliente or '').strip()
            clave = clave_cliente(nombre, telefono)

            if clave not in clientes_map:
                clientes_map[clave] = {
                    'selector_value': f'deudor:{nombre}:{telefono}',
                    'id': None,
                    'nombre': nombre,
                    'telefono': telefono,
                    'saldo_pendiente': Decimal('0'),
                    'tiene_saldo': False,
                }

            if saldo_pendiente > 0:
                clientes_map[clave]['saldo_pendiente'] += saldo_pendiente
                clientes_map[clave]['tiene_saldo'] = True

    clientes = list(clientes_map.values())
    clientes.sort(key=lambda cliente: (not cliente['tiene_saldo'], cliente['nombre'].lower(), cliente['telefono']))

    for cliente in clientes:
        cliente['saldo_pendiente'] = float(cliente['saldo_pendiente'])

    return clientes


def enriquecer_clientes_con_historial(clientes):
    """Agrega historial de compras y estado de cuenta a cada cliente del módulo de clientes."""
    clientes = list(clientes)
    claves_clientes = {
        ((cliente.nombre or '').strip().lower(), (cliente.telefono or '').strip())
        for cliente in clientes
        if (cliente.nombre or '').strip()
    }

    tareas_por_cliente = {}
    tareas = (
        TareaPlanificada.objects
        .prefetch_related('productos_tarea')
        .order_by('-fecha_ingreso', '-creado_en')
    )

    for tarea in tareas:
        clave = ((tarea.nombre_cliente or '').strip().lower(), (tarea.telefono_cliente or '').strip())
        if clave not in claves_clientes:
            continue
        tareas_por_cliente.setdefault(clave, []).append(tarea)

    for cliente in clientes:
        clave = ((cliente.nombre or '').strip().lower(), (cliente.telefono or '').strip())
        historial = tareas_por_cliente.get(clave, [])

        total_comprado = Decimal('0')
        total_abonado = Decimal('0')
        saldo_pendiente_total = Decimal('0')

        for tarea in historial:
            total_comprado += tarea.precio_total
            total_abonado += tarea.monto_abonado
            if tarea.saldo_pendiente > 0:
                saldo_pendiente_total += tarea.saldo_pendiente

        cliente.historial_compras = historial
        cliente.total_compras = len(historial)
        cliente.total_comprado = total_comprado
        cliente.total_abonado = total_abonado
        cliente.saldo_pendiente_total = saldo_pendiente_total
        cliente.debe = saldo_pendiente_total > 0
        cliente.ultima_compra = historial[0] if historial else None

    return clientes


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
            # Validar que el usuario tiene un perfil con rol válido
            try:
                perfil = user.perfil
                # Verificar que el rol sea válido
                if perfil.rol not in [choice[0] for choice in perfil._meta.get_field('rol').choices]:
                    messages.error(request, 'Tu usuario tiene un rol inválido. Contacta al administrador.')
                    return render(request, 'login.html')
            except Exception as e:
                messages.error(request, f'Error al validar tu perfil: {str(e)}')
                return render(request, 'login.html')
            
            login(request, user)
            rol_display = perfil.get_rol_display()
            messages.success(request, f'¡Bienvenido {user.username}! ({rol_display})')
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
    from decimal import Decimal
    from panelfinanzas.models import Gasto
    from panelproductividad.models import RegistroProductividad, Trabajador
    from django.db.models import Sum
    import json
    
    # Usar el rol del perfil para distinguir entre administración y trabajador.
    try:
        es_trabajador_logueado = request.user.perfil.es_trabajador and not request.user.is_superuser
    except (PerfilUsuario.DoesNotExist, AttributeError):
        es_trabajador_logueado = hasattr(request.user, 'trabajador') and not es_jefe(request.user)
    
    # Estadísticas generales
    tareas_pendientes = TareaPlanificada.objects.filter(estado='pendiente').count()
    tareas_en_proceso = TareaPlanificada.objects.filter(estado='en_proceso').count()
    tareas_completadas = TareaPlanificada.objects.filter(estado='completado').count()
    total_clientes = Cliente.objects.count()
    
    # Tareas próximas a entregar (próximos 7 días)
    hoy = date.today()
    proxima_semana = hoy + timedelta(days=7)
    tareas_proximas = TareaPlanificada.objects.filter(
        estado__in=['pendiente', 'en_proceso'],
        fecha_entrega__lte=proxima_semana
    ).order_by('fecha_entrega')[:5]
    
    # Tareas urgentes (vencidas o por vencer hoy)
    tareas_urgentes = TareaPlanificada.objects.filter(
        estado__in=['pendiente', 'en_proceso'],
        fecha_entrega__lte=hoy
    ).count()
    
    # -------------------------
    # COBRANZA Y CUENTAS POR COBRAR
    # -------------------------
    tareas_con_saldo_qs = TareaPlanificada.objects.exclude(estado='cancelado')
    saldo_total_pendiente = Decimal('0')
    tareas_sin_pagar_total = 0
    alertas_cobranza = []
    morosos_modal = []

    for tarea in tareas_con_saldo_qs:
        saldo = tarea.saldo_pendiente
        if saldo > 0:
            saldo_total_pendiente += saldo
            tareas_sin_pagar_total += 1
            dias_vencidos_desde_entrega = (hoy - tarea.fecha_entrega).days
            severidad = 'crítica' if dias_vencidos_desde_entrega > 30 else 'alta' if dias_vencidos_desde_entrega > 14 else 'media' if dias_vencidos_desde_entrega > 0 else 'pendiente'
            entry = {
                'tarea_id': tarea.id,
                'cliente': tarea.nombre_cliente,
                'telefono': tarea.telefono_cliente,
                'descripcion': tarea.descripcion_trabajo,
                'placa': tarea.placa or 'Sin placa',
                'total': tarea.precio_total,
                'abonado': tarea.monto_abonado,
                'saldo': saldo,
                'estado': tarea.get_estado_display(),
                'dias_vencidos': max(0, dias_vencidos_desde_entrega),
                'fecha_entrega': tarea.fecha_entrega,
                'severidad': severidad,
            }
            alertas_cobranza.append(entry)
            morosos_modal.append(entry)

    sort_key = lambda x: (x['severidad'] == 'pendiente', x['severidad'] != 'crítica', -x['dias_vencidos'])
    alertas_cobranza = sorted(alertas_cobranza, key=sort_key)[:5]
    morosos_modal = sorted(morosos_modal, key=sort_key)

    total_cobrado = tareas_con_saldo_qs.aggregate(total=Sum('monto_abonado'))['total'] or Decimal('0')

    # -------------------------
    # GASTOS Y PRESUPUESTO
    # -------------------------
    mes_actual = hoy.replace(day=1)
    if mes_actual.month == 12:
        ultimo_dia_mes = date(mes_actual.year, 12, 31)
    else:
        ultimo_dia_mes = (mes_actual.replace(month=mes_actual.month + 1, day=1) - timedelta(days=1))
    
    total_gastos_mes = Decimal('0')
    gastos_por_categoria = []
    gastos_labels = json.dumps([])
    gastos_data = json.dumps([])

    if not es_trabajador_logueado:
        gastos_mes = Gasto.objects.filter(
            fecha__gte=mes_actual,
            fecha__lte=ultimo_dia_mes
        )
        total_gastos_mes = sum(g.monto for g in gastos_mes)

        gastos_por_categoria = list(gastos_mes.values('categoria').annotate(
            total=Sum('monto')
        ).order_by('-total')[:5])

        # Preparar datos para gráfico de gastos
        if gastos_por_categoria:
            gastos_labels = json.dumps([g['categoria'] for g in gastos_por_categoria])
            gastos_data = json.dumps([float(g['total']) for g in gastos_por_categoria])
    
    # -------------------------
    # FLUJO DE CAJA PROYECTADO
    # -------------------------
    fecha_futura = hoy + timedelta(days=30)
    tareas_futuras = TareaPlanificada.objects.filter(
        fecha_entrega__gte=hoy,
        fecha_entrega__lte=fecha_futura,
        estado__in=['pendiente', 'en_proceso']
    )
    ingresos_esperados = sum(t.precio_total for t in tareas_futuras)
    gastos_proyectados = sum(g.monto for g in Gasto.objects.filter(
        fecha__gte=hoy,
        fecha__lte=fecha_futura
    ))
    
    # -------------------------
    # TAREAS CRÍTICAS
    # -------------------------
    tareas_criticas_qs = TareaPlanificada.objects.filter(
        estado__in=['pendiente', 'en_proceso'],
        fecha_entrega__lte=hoy + timedelta(days=7)
    ).order_by('fecha_entrega')[:3]
    
    tareas_criticas = []
    for tarea in tareas_criticas_qs:
        dias_restantes = (tarea.fecha_entrega - hoy).days
        tareas_criticas.append({
            'id': tarea.id,
            'nombre_cliente': tarea.nombre_cliente,
            'descripcion_trabajo': tarea.descripcion_trabajo,
            'fecha_entrega': tarea.fecha_entrega,
            'dias_restantes': max(0, dias_restantes),
        })
    
    # -------------------------
    # TRABAJADORES SIN REGISTRAR
    # -------------------------
    todos_trabajadores = Trabajador.objects.filter(activo=True)
    registrados_hoy = RegistroProductividad.objects.filter(fecha=hoy).values('trabajador_id').distinct()
    registrados_hoy_ids = [r['trabajador_id'] for r in registrados_hoy]
    trabajadores_sin_registrar = todos_trabajadores.exclude(id__in=registrados_hoy_ids)
    
    # -------------------------
    # TAREAS POR DÍA DE LA SEMANA
    # -------------------------
    # Calcular tareas completadas por día de la semana (últimos 7 días)
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    tareas_por_dia = [0] * 7
    
    # Obtener el lunes de la semana actual
    lunes_semana = hoy - timedelta(days=hoy.weekday())
    
    for i in range(7):
        dia_fecha = lunes_semana + timedelta(days=i)
        # Contar tareas completadas en esa fecha (usando fecha de actualización como aproximación)
        tareas_count = TareaPlanificada.objects.filter(
            estado='completado',
            actualizado_en__date=dia_fecha
        ).count()
        tareas_por_dia[i] = tareas_count
    
    tareas_semana_labels = json.dumps(dias_semana)
    tareas_semana_data = json.dumps(tareas_por_dia)
    
    context = {
        'tareas_pendientes': tareas_pendientes,
        'tareas_en_proceso': tareas_en_proceso,
        'tareas_completadas': tareas_completadas,
        'total_clientes': total_clientes,
        'tareas_proximas': tareas_proximas,
        'tareas_urgentes': tareas_urgentes,
        'es_trabajador': es_trabajador_logueado,
        # Cobranza
        'saldo_total_pendiente': saldo_total_pendiente,
        'tareas_sin_pagar_total': tareas_sin_pagar_total,
        'alertas_cobranza': alertas_cobranza,
        'morosos_modal': morosos_modal,
        'total_cobrado': total_cobrado,
        # Gastos
        'total_gastos_mes': total_gastos_mes,
        'gastos_por_categoria': gastos_por_categoria,
        'gastos_labels': gastos_labels,
        'gastos_data': gastos_data,
        # Flujo de Caja
        'ingresos_esperados': ingresos_esperados,
        'gastos_proyectados': gastos_proyectados,
        'flujo_proyectado': ingresos_esperados - gastos_proyectados,
        # Tareas Críticas
        'tareas_criticas': tareas_criticas,
        # Trabajadores
        'trabajadores_sin_registrar': list(trabajadores_sin_registrar),
        'primer_dia_mes': mes_actual,
        'ultimo_dia_mes': ultimo_dia_mes,
        # Tareas por día de la semana
        'tareas_semana_labels': tareas_semana_labels,
        'tareas_semana_data': tareas_semana_data,
    }
    return render(request, 'home.html', context)


@login_required
def lista_tareas(request):
    """Vista de lista de tareas con filtros y buscador"""
    usuario_es_jefe = es_jefe(request.user)

    filtro_estado = request.GET.get('estado', '').strip()
    filtro_prioridad = request.GET.get('prioridad', '').strip()
    filtro_placa = request.GET.get('placa', '').strip()
    filtro_cliente = request.GET.get('cliente', '').strip()

    tareas = TareaPlanificada.objects.all().order_by('-creado_en')

    if filtro_estado:
        tareas = tareas.filter(estado=filtro_estado)
    if filtro_prioridad:
        tareas = tareas.filter(prioridad=filtro_prioridad)
    if filtro_placa:
        tareas = tareas.filter(placa__icontains=filtro_placa)
    if filtro_cliente:
        tareas = tareas.filter(nombre_cliente__icontains=filtro_cliente)

    # Morosos: tareas completadas con saldo pendiente (solo visible para jefes/admins)
    morosos = []
    total_saldo_pendiente = Decimal('0')
    
    if usuario_es_jefe:
        for tarea in TareaPlanificada.objects.filter(estado='completado'):
            saldo = tarea.saldo_pendiente
            if saldo > 0:
                morosos.append({
                    'tarea': tarea,
                    'total': tarea.precio_total,
                    'abonado': tarea.monto_abonado,
                    'saldo': saldo,
                })
                total_saldo_pendiente += saldo

    return render(request, 'paneltareas/lista.html', {
        'tareas': tareas,
        'estados': TareaPlanificada.ESTADO_CHOICES,
        'prioridades': TareaPlanificada.PRIORIDAD_CHOICES,
        'morosos': morosos,
        'total_saldo_pendiente': total_saldo_pendiente,
        'es_jefe': usuario_es_jefe,
        'notas_activas': NotaTrabajo.objects.filter(tomada=False),
        'notas_tomadas': NotaTrabajo.objects.filter(tomada=True),
        'form_nota': NotaTrabajoForm(),
    })


@login_required
def crear_tarea(request):
    """Vista para crear una nueva tarea planificada con productos"""
    usuario_es_jefe = es_jefe(request.user)
    FormClass = TareaPlanificadaFormJefe if usuario_es_jefe else TareaPlanificadaForm
    
    if request.method == 'POST':
        form = FormClass(request.POST)
        formset = ProductoTareaFormSet(request.POST, prefix='productos')
        if form.is_valid() and formset.is_valid() and validar_imagenes_por_producto(formset, request.FILES):
            try:
                with transaction.atomic():
                    tarea = form.save(commit=False)
                    tarea.placa = ''
                    tarea.save()
                    # Auto-registrar cliente si no existe
                    Cliente.objects.get_or_create(
                        nombre=tarea.nombre_cliente,
                        defaults={'telefono': tarea.telefono_cliente}
                    )
                    formset.instance = tarea
                    total_imagenes = guardar_productos_tarea(formset, tarea, request.user, request.FILES)
            except ValidationError as exc:
                mensajes = obtener_mensajes_validacion(exc)
                messages.error(request, ' '.join(mensajes) or 'Error al guardar las imágenes de los productos.')
            else:
                if total_imagenes:
                    messages.success(request, f'Tarea creada exitosamente con {total_imagenes} imagen(es) asociadas a productos.')
                else:
                    messages.success(request, 'Tarea creada exitosamente.')
                return redirect('tareas:lista')
    else:
        form = FormClass(initial={'fecha_ingreso': date.today()})
        formset = ProductoTareaFormSet(prefix='productos')
    
    # Preparar datos de productos para JavaScript (autocompletar)
    productos_json = json.dumps([
        {
            'id': p.id,
            'nombre': p.nombre,
            'precio_venta': float(p.precio_venta),
            'precio_fijo': not p.es_precio_variable,
        }
        for p in Producto.objects.all()
    ])
    
    # Preparar datos de clientes para autocompletar, incluyendo saldos pendientes solo para jefes
    clientes_json = json.dumps(construir_clientes_formulario(mostrar_saldos=usuario_es_jefe))
    
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
        formset = ProductoTareaFormSetEdit(request.POST, instance=tarea, prefix='productos')
        if form.is_valid() and formset.is_valid() and validar_imagenes_por_producto(formset, request.FILES):
            try:
                with transaction.atomic():
                    form.save()
                    Cliente.objects.get_or_create(
                        nombre=tarea.nombre_cliente,
                        defaults={'telefono': tarea.telefono_cliente}
                    )
                    total_imagenes = guardar_productos_tarea(formset, tarea, request.user, request.FILES)
            except ValidationError as exc:
                mensajes = obtener_mensajes_validacion(exc)
                messages.error(request, ' '.join(mensajes) or 'Error al guardar las imágenes de los productos.')
            else:
                if total_imagenes:
                    messages.success(request, f'Tarea actualizada exitosamente con {total_imagenes} imagen(es) nuevas en productos.')
                else:
                    messages.success(request, 'Tarea actualizada exitosamente.')
                return redirect('tareas:lista')
    else:
        form = FormClass(instance=tarea)
        formset = ProductoTareaFormSetEdit(instance=tarea, prefix='productos')
    
    # Preparar datos de productos para JavaScript (autocompletar)
    productos_json = json.dumps([
        {
            'id': p.id,
            'nombre': p.nombre,
            'precio_venta': float(p.precio_venta),
            'precio_fijo': not p.es_precio_variable,
        }
        for p in Producto.objects.all()
    ])
    
    # Preparar datos de clientes para autocompletar, incluyendo saldos pendientes solo para jefes
    clientes_json = json.dumps(construir_clientes_formulario(mostrar_saldos=usuario_es_jefe))
    
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
    """Vista para ver el detalle de una tarea y subir múltiples imágenes"""
    tarea = get_object_or_404(
        TareaPlanificada.objects.prefetch_related('productos_tarea__imagenes', 'imagenes'),
        pk=pk,
    )
    usuario_es_jefe = es_jefe(request.user)
    
    if request.method == 'POST':
        # Procesar múltiples imágenes
        archivos = request.FILES.getlist('imagen')
        producto_tarea_id = request.POST.get('producto_tarea')
        descripcion = request.POST.get('descripcion', '')
        
        if archivos:
            contador = 0
            errores_procesar = []
            
            for archivo in archivos:
                try:
                    # 1. Comprimir la imagen INMEDIATAMENTE
                    contenido_comprimido, nombre_optimizado = _optimizar_imagen_bytes(archivo, archivo.name)
                    
                    # 2. Crear la imagen con el contenido comprimido
                    imagen = ImagenTarea(
                        tarea=tarea,
                        producto_tarea_id=producto_tarea_id if producto_tarea_id else None,
                        descripcion=descripcion
                    )
                    
                    # 3. Guardar el contenido comprimido directamente
                    nombre_base = Path(nombre_optimizado).name
                    imagen.imagen.save(nombre_base, ContentFile(contenido_comprimido), save=False)
                    imagen.full_clean()
                    imagen.save()
                    contador += 1
                except ValidationError as e:
                    errores_procesar.append(f"{archivo.name}: {', '.join(e.messages)}")
                except Exception as e:
                    errores_procesar.append(f"{archivo.name}: Error al comprimir/guardar")
            
            if contador > 0:
                plural = 'imagen' if contador == 1 else 'imágenes'
                messages.success(request, f'{contador} {plural} subida(s) y comprimida(s) exitosamente.')
            
            if errores_procesar:
                for error in errores_procesar[:3]:  # Mostrar máximo 3 errores
                    messages.error(request, error)
            
            return redirect('tareas:detalle', pk=pk)
        else:
            messages.error(request, 'Por favor selecciona al menos una imagen.')
    
    form_imagen = ImagenTareaForm(tarea=tarea)
    productos_tarea = tarea.productos_tarea.all()
    imagenes_generales = tarea.imagenes.activas().filter(producto_tarea__isnull=True)
    
    # Contar todas las imágenes de la tarea
    contador_imagenes = tarea.imagenes.count()
    
    form_abonar = AbonarForm()

    # Buscar cliente registrado para PDF/WhatsApp
    cliente_obj = Cliente.objects.filter(nombre__iexact=tarea.nombre_cliente).first()
    cliente_id = cliente_obj.pk if cliente_obj else None

    return render(request, 'paneltareas/detalle.html', {
        'tarea': tarea,
        'form_imagen': form_imagen,
        'imagenes_generales': imagenes_generales,
        'productos_tarea': productos_tarea,
        'es_jefe': usuario_es_jefe,
        'form_abonar': form_abonar,
        'cliente_id': cliente_id,
        'contador_imagenes': contador_imagenes,
    })


@login_required
def abonar_tarea(request, pk):
    """Vista para abonar dinero adicional a una tarea"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)

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
    """Vista para completar el pago total de una tarea"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)

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
    """Mueve una imagen a la papelera (soft-delete)"""
    tarea = get_object_or_404(TareaPlanificada, pk=pk)
    imagen = get_object_or_404(ImagenTarea, pk=imagen_pk, tarea=tarea)
    
    if request.method == 'POST':
        from django.utils import timezone
        imagen.eliminada = True
        imagen.eliminada_en = timezone.now()
        imagen.save(update_fields=['eliminada', 'eliminada_en'])
        messages.success(request, 'Imagen movida a la papelera. Puede restaurarse desde allí.')
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

    clientes = enriquecer_clientes_con_historial(clientes)
    
    # Verificar si el usuario es trabajador
    es_trabajador_logueado = False
    try:
        es_trabajador_logueado = request.user.perfil.es_trabajador and not request.user.is_superuser
    except (PerfilUsuario.DoesNotExist, AttributeError):
        es_trabajador_logueado = hasattr(request.user, 'trabajador') and not es_jefe(request.user)

    return render(request, 'paneltareas/clientes/lista.html', {
        'clientes': clientes,
        'es_trabajador': es_trabajador_logueado
    })


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


@require_not_trabajador
def reporte_cliente_pdf(request, pk):
    """Genera un PDF con el reporte de todas las tareas de un cliente"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    import os

    cliente = get_object_or_404(Cliente, pk=pk)
    tareas = TareaPlanificada.objects.filter(
        nombre_cliente__iexact=cliente.nombre
    ).prefetch_related('productos_tarea').order_by('-creado_en')

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('title', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#2980b9'), spaceAfter=4)
    style_subtitle = ParagraphStyle('subtitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#7f8c8d'), spaceAfter=12)
    style_section = ParagraphStyle('section', parent=styles['Normal'], fontSize=12, textColor=colors.white, fontName='Helvetica-Bold', spaceAfter=4)
    style_normal = ParagraphStyle('normal', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#34495e'))
    style_small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#7f8c8d'))
    style_total = ParagraphStyle('total', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#27ae60'), fontName='Helvetica-Bold')

    def fmt(value):
        try:
            n = int(Decimal(str(value)))
            return f"${n:,}".replace(',', '.')
        except Exception:
            return str(value)

    story = []

    # Encabezado
    story.append(Paragraph("Cuir Tapicería", style_title))
    story.append(Paragraph(f"Reporte de tareas — {cliente.nombre}", style_subtitle))
    story.append(Paragraph(f"Teléfono: {cliente.telefono or '—'}    |    Fecha: {date.today().strftime('%d/%m/%Y')}", style_small))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#3498db'), spaceAfter=12))

    if not tareas.exists():
        story.append(Paragraph("Este cliente no tiene tareas registradas.", style_normal))
    else:
        total_general = Decimal('0')
        total_abonado_general = Decimal('0')

        for tarea in tareas:
            # Encabezado de tarea
            estado_label = dict(TareaPlanificada.ESTADO_CHOICES).get(tarea.estado, tarea.estado)
            placa_str = tarea.placa or 'Sin placa'
            header_data = [[
                Paragraph(f"<b>{placa_str}</b>  —  {tarea.fecha_ingreso.strftime('%d/%m/%Y')} → {tarea.fecha_entrega.strftime('%d/%m/%Y')}  |  Estado: {estado_label}", style_normal),
            ]]
            header_table = Table(header_data, colWidths=[doc.width])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2980b9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(header_table)

            productos = tarea.productos_tarea.all()
            if productos.exists():
                prod_data = [['Producto', 'Placa', 'Cant.', 'P. Venta', 'Total']]
                for pt in productos:
                    desc = pt.descripcion or ''
                    nombre_cell = Paragraph(f"<b>{pt.nombre_producto}</b><br/><font size='7' color='grey'>{desc}</font>" if desc else f"<b>{pt.nombre_producto}</b>", style_normal)
                    prod_data.append([
                        nombre_cell,
                        pt.placa or '—',
                        str(pt.cantidad),
                        fmt(pt.precio_venta),
                        fmt(pt.total_venta),
                    ])

                col_widths = [doc.width * 0.38, doc.width * 0.15, doc.width * 0.08, doc.width * 0.18, doc.width * 0.18]
                prod_table = Table(prod_data, colWidths=col_widths)
                prod_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
                    ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(prod_table)

            # Imágenes de proceso por producto
            MAX_FOTOS = 4
            IMG_W = doc.width / MAX_FOTOS - 0.3 * cm
            IMG_H = IMG_W * 0.75
            for pt in productos:
                imagenes = pt.imagenes.activas()[:MAX_FOTOS * 2]  # máx 8 fotos por producto, solo activas
                if imagenes:
                    story.append(Paragraph(
                        f"<b>Fotos del proceso — {pt.nombre_producto}</b>",
                        ParagraphStyle('foto_label', parent=styles['Normal'], fontSize=7,
                                       textColor=colors.HexColor('#7f8c8d'), spaceBefore=3, spaceAfter=2)
                    ))
                    # Agrupar en filas de MAX_FOTOS
                    batch = []
                    rows_img = []
                    for img_obj in imagenes:
                        img_path = img_obj.imagen.path if hasattr(img_obj.imagen, 'path') else None
                        if img_path and os.path.exists(img_path):
                            try:
                                rl_img = RLImage(img_path, width=IMG_W, height=IMG_H)
                                batch.append(rl_img)
                            except Exception:
                                pass
                        if len(batch) == MAX_FOTOS:
                            rows_img.append(batch)
                            batch = []
                    if batch:
                        # Pad row with empty strings to keep columns even
                        while len(batch) < MAX_FOTOS:
                            batch.append('')
                        rows_img.append(batch)
                    if rows_img:
                        img_table = Table(rows_img, colWidths=[IMG_W] * MAX_FOTOS)
                        img_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ('LEFTPADDING', (0, 0), (-1, -1), 2),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                        ]))
                        story.append(img_table)
                        story.append(Spacer(1, 4))

            # Fila resumen de pago
            resumen_data = [[
                Paragraph(f"Total: <b>{fmt(tarea.precio_total)}</b>   Abonado: <b>{fmt(tarea.monto_abonado)}</b>   Saldo pendiente: <b>{fmt(tarea.saldo_pendiente)}</b>", style_normal),
            ]]
            resumen_table = Table(resumen_data, colWidths=[doc.width])
            bg_color = colors.HexColor('#d5f5e3') if tarea.saldo_pendiente == 0 else colors.HexColor('#fdecea')
            resumen_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(resumen_table)
            story.append(Spacer(1, 10))

            total_general += tarea.precio_total
            total_abonado_general += tarea.monto_abonado

        # Resumen general
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#3498db'), spaceBefore=4, spaceAfter=8))
        saldo_general = total_general - total_abonado_general
        resumen_general_data = [
            ['Total facturado', 'Total abonado', 'Saldo pendiente'],
            [fmt(total_general), fmt(total_abonado_general), fmt(saldo_general)],
        ]
        resumen_general_table = Table(resumen_general_data, colWidths=[doc.width / 3] * 3)
        resumen_general_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980b9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#e74c3c') if saldo_general > 0 else colors.HexColor('#27ae60')),
        ]))
        story.append(resumen_general_table)

    doc.build(story)
    buffer.seek(0)

    nombre_safe = unicodedata.normalize('NFKD', cliente.nombre).encode('ascii', 'ignore').decode('ascii')
    nombre_safe = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in nombre_safe).strip().replace(' ', '_')

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{nombre_safe}.pdf"'
    return response


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


# =============================================
# VISTAS DE PAPELERA DE IMAGENES
# =============================================

@require_not_trabajador
def papelera_imagenes(request):
    imagenes = ImagenTarea.objects.papelera().select_related('tarea', 'producto_tarea').order_by('-eliminada_en')
    return render(request, 'paneltareas/papelera.html', {
        'imagenes': imagenes,
    })


@require_not_trabajador
def restaurar_imagen(request, imagen_pk):
    imagen = get_object_or_404(ImagenTarea, pk=imagen_pk)
    if request.method == 'POST':
        imagen.eliminada = False
        imagen.eliminada_en = None
        imagen.save(update_fields=['eliminada', 'eliminada_en'])
        messages.success(request, 'Imagen restaurada exitosamente.')
    return redirect('tareas:papelera')


@require_not_trabajador
def eliminar_permanente_imagen(request, imagen_pk):
    imagen = get_object_or_404(ImagenTarea, pk=imagen_pk)
    if request.method == 'POST':
        if imagen.imagen:
            imagen.imagen.delete(save=False)
        imagen.delete()
        messages.success(request, 'Imagen eliminada definitivamente.')
    return redirect('tareas:papelera')


@require_not_trabajador
def vaciar_papelera(request):
    if request.method == 'POST':
        eliminadas = ImagenTarea.objects.papelera()
        count = eliminadas.count()
        for img in eliminadas:
            if img.imagen:
                img.imagen.delete(save=False)
            img.delete()
        messages.success(request, f'Se eliminaron {count} imagen(es) definitivamente.')
    return redirect('tareas:papelera')


# =============================================
# VISTA DE ANOTACION DE IMAGEN
# =============================================

@login_required
def anotar_imagen(request, imagen_pk):
    imagen = get_object_or_404(ImagenTarea, pk=imagen_pk)

    if request.method == 'POST':
        archivo = request.FILES.get('imagen_anotada')
        if archivo:
            if imagen.imagen:
                imagen.imagen.delete(save=False)
            from pathlib import Path
            import os
            nombre_archivo = Path(archivo.name).name
            imagen._omitir_optimizacion_imagen = False
            imagen.imagen.save(nombre_archivo, archivo, save=False)
            from .models import programar_optimizacion_imagen
            from django.db import transaction
            imagen.save()
            transaction.on_commit(lambda: programar_optimizacion_imagen(imagen.pk))
            messages.success(request, 'Anotación guardada.')
        else:
            messages.error(request, 'No se recibió la imagen anotada.')
        return redirect('tareas:detalle', pk=imagen.tarea_id)

    return redirect('tareas:detalle', pk=imagen.tarea_id)


# =============================================
# VISTAS DE NOTAS DE TRABAJO
# =============================================

@login_required
def crear_nota_trabajo(request):
    if request.method == 'POST':
        form = NotaTrabajoForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.creado_por = request.user
            nota.save()
            messages.success(request, 'Nota guardada.')
        else:
            messages.error(request, 'Error al guardar la nota.')
    return redirect('tareas:lista')


@login_required
def toggle_tomada_nota(request, nota_pk):
    nota = get_object_or_404(NotaTrabajo, pk=nota_pk)
    if request.method == 'POST':
        from django.utils import timezone
        nota.tomada = not nota.tomada
        nota.tomada_en = timezone.now() if nota.tomada else None
        nota.save(update_fields=['tomada', 'tomada_en'])
        if nota.tomada:
            messages.success(request, 'Nota marcada como tomada.')
        else:
            messages.success(request, 'Nota reabierta.')
    return redirect('tareas:lista')


@login_required
def eliminar_nota_trabajo(request, nota_pk):
    nota = get_object_or_404(NotaTrabajo, pk=nota_pk)
    if request.method == 'POST':
        nota.delete()
        messages.success(request, 'Nota eliminada.')
    return redirect('tareas:lista')


# =============================================
# VISTAS DE EXPORTACION Y BORRADO MASIVO DE TAREAS
# =============================================

@require_not_trabajador
def exportar_tareas_csv(request):
    import csv
    ids_str = request.GET.get('tarea_ids', '')
    if not ids_str:
        messages.warning(request, 'No se seleccionó ninguna tarea.')
        return redirect('tareas:lista')

    try:
        ids = [int(x) for x in ids_str.split(',') if x.strip().isdigit()]
    except (ValueError, TypeError):
        messages.error(request, 'Selección inválida.')
        return redirect('tareas:lista')

    tareas = TareaPlanificada.objects.filter(pk__in=ids).prefetch_related('productos_tarea').order_by('-creado_en')
    if not tareas.exists():
        messages.warning(request, 'No se encontraron tareas con esos IDs.')
        return redirect('tareas:lista')

    fecha_str = date.today().strftime('%Y%m%d')
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="tareas_export_{fecha_str}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'tarea_id', 'cliente', 'telefono', 'fecha_ingreso', 'fecha_entrega',
        'estado', 'prioridad', 'categoria', 'placa',
        'producto', 'cantidad', 'precio_costo', 'precio_venta',
        'total_producto', 'precio_total_tarea', 'monto_abonado', 'saldo_pendiente',
    ])

    for tarea in tareas:
        productos = tarea.productos_tarea.all()
        if productos:
            for pt in productos:
                writer.writerow([
                    tarea.id, tarea.nombre_cliente, tarea.telefono_cliente,
                    tarea.fecha_ingreso.isoformat(), tarea.fecha_entrega.isoformat(),
                    tarea.estado, tarea.prioridad, tarea.categoria, tarea.placa or '',
                    pt.nombre_producto, pt.cantidad,
                    float(pt.precio_costo), float(pt.precio_venta),
                    float(pt.total_venta), float(tarea.precio_total),
                    float(tarea.monto_abonado), float(tarea.saldo_pendiente),
                ])
        else:
            writer.writerow([
                tarea.id, tarea.nombre_cliente, tarea.telefono_cliente,
                tarea.fecha_ingreso.isoformat(), tarea.fecha_entrega.isoformat(),
                tarea.estado, tarea.prioridad, tarea.categoria, tarea.placa or '',
                '', 0, 0, 0, 0,
                float(tarea.precio_total), float(tarea.monto_abonado), float(tarea.saldo_pendiente),
            ])

    messages.success(request, f'Se exportaron {tareas.count()} tarea(s) a CSV.')
    return response


@require_not_trabajador
def borrar_seleccionadas(request):
    if request.method != 'POST':
        return redirect('tareas:lista')

    ids_str = request.POST.get('tarea_ids', '')
    if not ids_str:
        messages.warning(request, 'No se seleccionó ninguna tarea.')
        return redirect('tareas:lista')

    try:
        ids = [int(x) for x in ids_str.split(',') if x.strip().isdigit()]
    except (ValueError, TypeError):
        messages.error(request, 'Selección inválida.')
        return redirect('tareas:lista')

    tareas = TareaPlanificada.objects.filter(pk__in=ids)
    count = tareas.count()
    with transaction.atomic():
        for tarea in tareas:
            for img in tarea.imagenes.all():
                if img.imagen:
                    img.imagen.delete(save=False)
            tarea.delete()

    messages.success(request, f'Se eliminaron {count} tarea(s) y sus imágenes.')
    return redirect('tareas:lista')
