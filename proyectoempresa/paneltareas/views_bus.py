"""
Vistas para el módulo de Bus.
Filtra/guarda tareas con categoria='bus'.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import date
from decimal import Decimal
import json

from .models import TareaPlanificada, ProductoTarea
from .forms import (
    TareaPlanificadaForm,
    TareaPlanificadaFormJefe,
    ProductoTareaFormSet,
    ProductoTareaFormSetEdit,
    AbonarForm,
)
from .views import (
    es_jefe,
    construir_clientes_formulario,
    guardar_productos_tarea,
    validar_imagenes_por_producto,
    obtener_mensajes_validacion,
)
from panelfinanzas.models import Producto

# Clientes permitidos en el módulo de Bus
NOMBRES_CLIENTES_BUS = ['solobus', 'namired']


def construir_clientes_bus(mostrar_saldos=False):
    """Devuelve solo los clientes de bus (Solobus y Namired)."""
    todos = construir_clientes_formulario(mostrar_saldos=mostrar_saldos)
    filtrados = [c for c in todos if c['nombre'].lower() in NOMBRES_CLIENTES_BUS]

    # Asegurar que ambos clientes aparezcan aunque no existan en DB aún
    nombres_presentes = {c['nombre'].lower() for c in filtrados}
    for nombre in NOMBRES_CLIENTES_BUS:
        if nombre not in nombres_presentes:
            filtrados.append({
                'selector_value': f'nombre:{nombre.capitalize()}',
                'id': None,
                'nombre': nombre.capitalize(),
                'telefono': '',
                'saldo_pendiente': 0.0,
                'tiene_saldo': False,
            })

    filtrados.sort(key=lambda c: c['nombre'].lower())
    return filtrados


def productos_bus_json():
    """Devuelve JSON solo con los productos marcados como de Bus."""
    return json.dumps([
        {
            'id': p.id,
            'nombre': p.nombre,
            'precio_venta': float(p.precio_venta),
            'precio_fijo': not p.es_precio_variable,
        }
        for p in Producto.objects.filter(es_bus=True)
    ])


# ---------------------------------------------------------------------------
# Lista de tareas de Bus
# ---------------------------------------------------------------------------

@login_required
def lista_tareas_bus(request):
    usuario_es_jefe = es_jefe(request.user)

    filtro_estado = request.GET.get('estado', '').strip()
    filtro_prioridad = request.GET.get('prioridad', '').strip()
    filtro_placa = request.GET.get('placa', '').strip()
    filtro_cliente = request.GET.get('cliente', '').strip()

    tareas = TareaPlanificada.objects.filter(categoria='bus').order_by('-creado_en')

    if filtro_estado:
        tareas = tareas.filter(estado=filtro_estado)
    if filtro_prioridad:
        tareas = tareas.filter(prioridad=filtro_prioridad)
    if filtro_placa:
        tareas = tareas.filter(placa__icontains=filtro_placa)
    if filtro_cliente:
        tareas = tareas.filter(nombre_cliente__icontains=filtro_cliente)

    morosos = []
    total_saldo_pendiente = Decimal('0')

    if usuario_es_jefe:
        for tarea in TareaPlanificada.objects.filter(estado='completado', categoria='bus'):
            saldo = tarea.saldo_pendiente
            if saldo > 0:
                morosos.append({
                    'tarea': tarea,
                    'total': tarea.precio_total,
                    'abonado': tarea.monto_abonado,
                    'saldo': saldo,
                })
                total_saldo_pendiente += saldo

    return render(request, 'panelbus/lista.html', {
        'tareas': tareas,
        'estados': TareaPlanificada.ESTADO_CHOICES,
        'prioridades': TareaPlanificada.PRIORIDAD_CHOICES,
        'morosos': morosos,
        'total_saldo_pendiente': total_saldo_pendiente,
        'es_jefe': usuario_es_jefe,
    })


# ---------------------------------------------------------------------------
# Crear tarea de Bus
# ---------------------------------------------------------------------------

@login_required
def crear_tarea_bus(request):
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
                    tarea.categoria = 'bus'
                    tarea.save()
                    from .models import Cliente
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
                    messages.success(request, f'Tarea Bus creada exitosamente con {total_imagenes} imagen(es) asociadas a productos.')
                else:
                    messages.success(request, 'Tarea Bus creada exitosamente.')
                return redirect('bus:lista')
    else:
        form = FormClass(initial={'fecha_ingreso': date.today()})
        formset = ProductoTareaFormSet(prefix='productos')

    productos_json = productos_bus_json()
    clientes_json = json.dumps(construir_clientes_bus(mostrar_saldos=usuario_es_jefe))
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
        'modulo_bus': True,
    })


# ---------------------------------------------------------------------------
# Editar tarea de Bus
# ---------------------------------------------------------------------------

@login_required
def editar_tarea_bus(request, pk):
    tarea = get_object_or_404(TareaPlanificada, pk=pk, categoria='bus')
    usuario_es_jefe = es_jefe(request.user)
    FormClass = TareaPlanificadaFormJefe if usuario_es_jefe else TareaPlanificadaForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=tarea)
        formset = ProductoTareaFormSetEdit(request.POST, instance=tarea, prefix='productos')
        if form.is_valid() and formset.is_valid() and validar_imagenes_por_producto(formset, request.FILES):
            try:
                with transaction.atomic():
                    tarea_saved = form.save(commit=False)
                    tarea_saved.categoria = 'bus'  # mantener categoría
                    tarea_saved.save()
                    from .models import Cliente
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
                    messages.success(request, f'Tarea Bus actualizada exitosamente con {total_imagenes} imagen(es) nuevas.')
                else:
                    messages.success(request, 'Tarea Bus actualizada exitosamente.')
                return redirect('bus:lista')
    else:
        form = FormClass(instance=tarea)
        formset = ProductoTareaFormSetEdit(instance=tarea, prefix='productos')

    productos_json = productos_bus_json()
    clientes_json = json.dumps(construir_clientes_bus(mostrar_saldos=usuario_es_jefe))
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
        'modulo_bus': True,
    })


# ---------------------------------------------------------------------------
# Eliminar tarea de Bus
# ---------------------------------------------------------------------------

@login_required
def eliminar_tarea_bus(request, pk):
    tarea = get_object_or_404(TareaPlanificada, pk=pk, categoria='bus')

    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea Bus eliminada exitosamente.')
        return redirect('bus:lista')

    return render(request, 'paneltareas/eliminar.html', {
        'tarea': tarea,
        'modulo_bus': True,
    })


# ---------------------------------------------------------------------------
# Cambiar estado de tarea Bus
# ---------------------------------------------------------------------------

@login_required
def cambiar_estado_bus(request, pk, estado):
    tarea = get_object_or_404(TareaPlanificada, pk=pk, categoria='bus')
    estados_validos = dict(TareaPlanificada.ESTADO_CHOICES).keys()

    if estado in estados_validos:
        tarea.estado = estado
        tarea.save()
        messages.success(request, f'Estado cambiado a {tarea.get_estado_display()}.')
    else:
        messages.error(request, 'Estado no válido.')

    return redirect('bus:lista')
