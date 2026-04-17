from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from datetime import date, timedelta
from decimal import Decimal
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


def construir_clientes_formulario():
    """Construye la lista de clientes para el selector y autocompletado, incluyendo saldos pendientes."""
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
    tareas_completadas_qs = TareaPlanificada.objects.filter(estado='completado')
    saldo_total_pendiente = Decimal('0')
    tareas_sin_pagar_total = 0
    alertas_cobranza = []
    
    for tarea in tareas_completadas_qs:
        saldo = tarea.saldo_pendiente
        if saldo > 0:
            saldo_total_pendiente += saldo
            tareas_sin_pagar_total += 1
            dias_vencidos_desde_entrega = (hoy - tarea.fecha_entrega).days
            if dias_vencidos_desde_entrega > 0:
                alertas_cobranza.append({
                    'tarea_id': tarea.id,
                    'cliente': tarea.nombre_cliente,
                    'saldo': saldo,
                    'dias_vencidos': dias_vencidos_desde_entrega,
                    'fecha_entrega': tarea.fecha_entrega,
                    'severidad': 'crítica' if dias_vencidos_desde_entrega > 30 else 'alta' if dias_vencidos_desde_entrega > 14 else 'media',
                })
    
    alertas_cobranza = sorted(alertas_cobranza, key=lambda x: (x['severidad'] != 'crítica', -x['dias_vencidos']))[:5]
    
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
    }
    return render(request, 'home.html', context)


@login_required
def lista_tareas(request):
    """Redirige a la página principal del Kanban"""
    return redirect('tareas:kanban')


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
    
    # Preparar datos de clientes para autocompletar, incluyendo saldos pendientes
    clientes_json = json.dumps(construir_clientes_formulario())
    
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
        formset = ProductoTareaFormSet(instance=tarea, prefix='productos')
    
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
    
    # Preparar datos de clientes para autocompletar, incluyendo saldos pendientes
    clientes_json = json.dumps(construir_clientes_formulario())
    
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
    tarea = get_object_or_404(
        TareaPlanificada.objects.prefetch_related('productos_tarea__imagenes', 'imagenes'),
        pk=pk,
    )
    usuario_es_jefe = es_jefe(request.user)
    
    if request.method == 'POST':
        form_imagen = ImagenTareaForm(request.POST, request.FILES, tarea=tarea)
        if form_imagen.is_valid():
            imagen = form_imagen.save(commit=False)
            imagen.tarea = tarea
            imagen.save()
            messages.success(request, f'Imagen subida exitosamente para {imagen.producto_tarea.nombre_producto}.')
            return redirect('tareas:detalle', pk=pk)
        else:
            mensajes = []
            for errores in form_imagen.errors.values():
                mensajes.extend(errores)
            messages.error(request, ' '.join(mensajes) or 'Error al subir la imagen. Verifica que sea un archivo de imagen válido.')
    else:
        form_imagen = ImagenTareaForm(tarea=tarea)
    
    productos_tarea = tarea.productos_tarea.all()
    imagenes_generales = tarea.imagenes.filter(producto_tarea__isnull=True)
    
    form_abonar = AbonarForm()

    return render(request, 'paneltareas/detalle.html', {
        'tarea': tarea,
        'form_imagen': form_imagen,
        'imagenes_generales': imagenes_generales,
        'productos_tarea': productos_tarea,
        'es_jefe': usuario_es_jefe,
        'form_abonar': form_abonar,
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

    clientes = enriquecer_clientes_con_historial(clientes)

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
