from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count, F, Q, DecimalField, FloatField
from django.db.models.functions import TruncMonth, TruncWeek, ExtractWeekDay
from functools import wraps
from datetime import date, timedelta, datetime
from decimal import Decimal
from collections import defaultdict
import json

from .models import ObjetivoMensual, NotaAnalisis
from .forms import FiltroAnalisisForm, ObjetivoMensualForm, NotaAnalisisForm
from paneltareas.models import TareaPlanificada, Cliente, ProductoTarea
from panelproductividad.models import RegistroProductividad, Trabajador
from panelfinanzas.models import Producto, CategoriaProducto, PerfilUsuario


# =============================================
# DECORADORES
# =============================================

def solo_jefes(view_func):
    """Solo permite acceso a jefes y superusuarios"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if not request.user.perfil.es_jefe:
                messages.error(request, 'No tienes permisos para acceder al panel de análisis.')
                return redirect('home')
        except PerfilUsuario.DoesNotExist:
            messages.error(request, 'Tu usuario no tiene un perfil configurado.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def _obtener_rango_fechas(request):
    """Obtiene el rango de fechas del request o usa valores por defecto (mes actual)"""
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
    
    return fecha_desde, fecha_hasta


def _calcular_variacion(actual, anterior):
    """Calcula el porcentaje de variación entre dos valores"""
    if anterior and anterior > 0:
        return round(((actual - anterior) / anterior) * 100, 1)
    return 0


# =============================================
# VISTA PRINCIPAL - DASHBOARD DE KPIs
# =============================================

@solo_jefes
def dashboard_analisis(request):
    """Dashboard principal de análisis con KPIs clave"""
    fecha_desde, fecha_hasta = _obtener_rango_fechas(request)
    form_filtro = FiltroAnalisisForm(initial={
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta
    })
    
    # Calcular duración del período y período anterior para comparación
    dias_periodo = (fecha_hasta - fecha_desde).days + 1
    fecha_anterior_hasta = fecha_desde - timedelta(days=1)
    fecha_anterior_desde = fecha_anterior_hasta - timedelta(days=dias_periodo - 1)
    
    # -------------------------
    # KPIs FINANCIEROS
    # -------------------------
    entregas = ProductoTarea.objects.filter(
        fecha_registro__date__gte=fecha_desde,
        fecha_registro__date__lte=fecha_hasta
    )
    entregas_anterior = ProductoTarea.objects.filter(
        fecha_registro__date__gte=fecha_anterior_desde,
        fecha_registro__date__lte=fecha_anterior_hasta
    )
    
    # Ingresos totales
    ingresos = Decimal('0')
    costos = Decimal('0')
    for e in entregas:
        ingresos += e.total_venta
        costos += e.total_costo
    ganancia = ingresos - costos
    margen = round((ganancia / ingresos * 100), 1) if ingresos > 0 else 0
    
    ingresos_anterior = Decimal('0')
    costos_anterior = Decimal('0')
    for e in entregas_anterior:
        ingresos_anterior += e.total_venta
        costos_anterior += e.total_costo
    ganancia_anterior = ingresos_anterior - costos_anterior
    
    var_ingresos = _calcular_variacion(float(ingresos), float(ingresos_anterior))
    var_ganancia = _calcular_variacion(float(ganancia), float(ganancia_anterior))
    
    # Ticket promedio (ingreso promedio por tarea)
    tareas_con_productos = entregas.values('tarea').distinct().count()
    ticket_promedio = ingresos / tareas_con_productos if tareas_con_productos > 0 else Decimal('0')
    
    # -------------------------
    # KPIs OPERATIVOS
    # -------------------------
    tareas_periodo = TareaPlanificada.objects.filter(
        fecha_ingreso__gte=fecha_desde,
        fecha_ingreso__lte=fecha_hasta
    )
    tareas_completadas = tareas_periodo.filter(estado='completado').count()
    tareas_total = tareas_periodo.count()
    tasa_completacion = round((tareas_completadas / tareas_total * 100), 1) if tareas_total > 0 else 0
    
    # Tareas período anterior
    tareas_anterior = TareaPlanificada.objects.filter(
        fecha_ingreso__gte=fecha_anterior_desde,
        fecha_ingreso__lte=fecha_anterior_hasta
    )
    tareas_completadas_ant = tareas_anterior.filter(estado='completado').count()
    var_tareas = _calcular_variacion(tareas_completadas, tareas_completadas_ant)
    
    # Tiempo promedio de entrega (días entre ingreso y entrega)
    tareas_completadas_qs = TareaPlanificada.objects.filter(
        estado='completado',
        fecha_ingreso__gte=fecha_desde,
        fecha_ingreso__lte=fecha_hasta
    )
    tiempos_entrega = []
    for t in tareas_completadas_qs:
        delta = (t.fecha_entrega - t.fecha_ingreso).days
        if delta >= 0:
            tiempos_entrega.append(delta)
    tiempo_promedio = round(sum(tiempos_entrega) / len(tiempos_entrega), 1) if tiempos_entrega else 0
    
    # Tareas vencidas (pasaron de la fecha de entrega sin completar)
    hoy = date.today()
    tareas_vencidas = TareaPlanificada.objects.filter(
        estado__in=['pendiente', 'en_proceso'],
        fecha_entrega__lt=hoy
    ).count()
    
    # Tasa de cumplimiento (entregas a tiempo vs total completadas)
    total_completadas_general = TareaPlanificada.objects.filter(estado='completado')
    entregas_a_tiempo = 0
    for t in total_completadas_general.filter(
        fecha_ingreso__gte=fecha_desde,
        fecha_ingreso__lte=fecha_hasta
    ):
        if t.fecha_entrega >= t.fecha_ingreso:
            entregas_a_tiempo += 1
    tasa_puntualidad = round(
        (entregas_a_tiempo / tareas_completadas * 100), 1
    ) if tareas_completadas > 0 else 0
    
    # -------------------------
    # KPIs DE PRODUCTIVIDAD
    # -------------------------
    registros_prod = RegistroProductividad.objects.filter(
        fecha__gte=fecha_desde,
        fecha__lte=fecha_hasta
    )
    total_items_producidos = 0
    total_horas_trabajo = 0
    for r in registros_prod:
        total_items_producidos += r.total_items
        # Calcular horas
        inicio = datetime.combine(r.fecha, r.hora_inicio)
        fin = datetime.combine(r.fecha, r.hora_finalizacion)
        if fin < inicio:
            fin += timedelta(days=1)
        horas = (fin - inicio).seconds / 3600
        total_horas_trabajo += horas
    
    productividad_hora = round(total_items_producidos / total_horas_trabajo, 1) if total_horas_trabajo > 0 else 0
    
    registros_prod_ant = RegistroProductividad.objects.filter(
        fecha__gte=fecha_anterior_desde,
        fecha__lte=fecha_anterior_hasta
    )
    items_ant = sum(r.total_items for r in registros_prod_ant)
    var_productividad = _calcular_variacion(total_items_producidos, items_ant)
    
    # -------------------------
    # KPIs DE CLIENTES
    # -------------------------
    clientes_nuevos = Cliente.objects.filter(
        creado_en__date__gte=fecha_desde,
        creado_en__date__lte=fecha_hasta
    ).count()
    total_clientes = Cliente.objects.count()
    
    clientes_nuevos_ant = Cliente.objects.filter(
        creado_en__date__gte=fecha_anterior_desde,
        creado_en__date__lte=fecha_anterior_hasta
    ).count()
    var_clientes = _calcular_variacion(clientes_nuevos, clientes_nuevos_ant)
    
    # -------------------------
    # DATOS PARA GRÁFICAS
    # -------------------------
    
    # Gráfica de ingresos por semana/mes
    entregas_por_mes = ProductoTarea.objects.filter(
        fecha_registro__date__gte=fecha_desde - timedelta(days=180),
        fecha_registro__date__lte=fecha_hasta
    ).annotate(
        mes=TruncMonth('fecha_registro')
    ).values('mes').annotate(
        total_venta=Sum(F('precio_venta') * F('cantidad'), output_field=DecimalField()),
        total_costo=Sum(F('precio_costo') * F('cantidad'), output_field=DecimalField()),
    ).order_by('mes')
    
    labels_ingresos = []
    data_ingresos = []
    data_costos_chart = []
    data_ganancia_chart = []
    for item in entregas_por_mes:
        labels_ingresos.append(item['mes'].strftime('%b %Y'))
        venta = float(item['total_venta'] or 0)
        costo = float(item['total_costo'] or 0)
        data_ingresos.append(venta)
        data_costos_chart.append(costo)
        data_ganancia_chart.append(round(venta - costo, 2))
    
    # Gráfica de tareas por estado
    tareas_por_estado = TareaPlanificada.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')
    
    estado_labels = []
    estado_data = []
    estado_colors = {
        'pendiente': '#f39c12',
        'en_proceso': '#3498db',
        'completado': '#27ae60',
        'cancelado': '#95a5a6',
    }
    estado_bg = []
    for item in tareas_por_estado:
        estado_dict = dict(TareaPlanificada.ESTADO_CHOICES)
        estado_labels.append(estado_dict.get(item['estado'], item['estado']))
        estado_data.append(item['total'])
        estado_bg.append(estado_colors.get(item['estado'], '#ccc'))
    
    # Gráfica de productividad por proceso
    proc_fields = ['cortado', 'marcado_piezas', 'costura', 'armado', 
                   'instalacion', 'sillas_realizadas', 'tapizado_puertas', 'tapizado_techo']
    proc_labels = ['Cortado', 'Marcado', 'Costura', 'Armado', 
                   'Instalación', 'Sillas', 'Tap. Puertas', 'Tap. Techo']
    proc_totals = []
    aggs = registros_prod.aggregate(**{f'total_{f}': Sum(f) for f in proc_fields})
    for f in proc_fields:
        proc_totals.append(aggs[f'total_{f}'] or 0)
    
    # Top productos más vendidos
    top_productos = entregas.values('nombre_producto').annotate(
        total_cant=Sum('cantidad'),
        total_ingreso=Sum(F('precio_venta') * F('cantidad'), output_field=DecimalField()),
    ).order_by('-total_cant')[:10]
    
    top_prod_labels = [p['nombre_producto'] for p in top_productos]
    top_prod_data = [p['total_cant'] for p in top_productos]
    
    # -------------------------
    # OBJETIVO MENSUAL (si existe)
    # -------------------------
    mes_actual = hoy.replace(day=1)
    objetivo = ObjetivoMensual.objects.filter(mes=mes_actual).first()
    
    progreso_objetivo = None
    if objetivo:
        # Datos del mes actual para comparar con objetivo
        primer_dia_mes = mes_actual
        ultimo_dia_mes = (mes_actual.replace(month=mes_actual.month % 12 + 1, day=1) - timedelta(days=1)) if mes_actual.month < 12 else date(mes_actual.year, 12, 31)
        
        entregas_mes = ProductoTarea.objects.filter(
            fecha_registro__date__gte=primer_dia_mes,
            fecha_registro__date__lte=ultimo_dia_mes
        )
        ingresos_mes = sum(e.total_venta for e in entregas_mes)
        ganancia_mes = sum(e.ganancia_total for e in entregas_mes)
        tareas_mes = TareaPlanificada.objects.filter(
            estado='completado',
            fecha_ingreso__gte=primer_dia_mes,
            fecha_ingreso__lte=ultimo_dia_mes
        ).count()
        clientes_mes = Cliente.objects.filter(
            creado_en__date__gte=primer_dia_mes,
            creado_en__date__lte=ultimo_dia_mes
        ).count()
        items_mes = sum(r.total_items for r in RegistroProductividad.objects.filter(
            fecha__gte=primer_dia_mes,
            fecha__lte=ultimo_dia_mes
        ))
        
        progreso_objetivo = {
            'ingresos': {
                'actual': ingresos_mes,
                'meta': objetivo.meta_ingresos,
                'porcentaje': min(round(float(ingresos_mes) / float(objetivo.meta_ingresos) * 100, 1), 100) if objetivo.meta_ingresos > 0 else 0,
            },
            'ganancia': {
                'actual': ganancia_mes,
                'meta': objetivo.meta_ganancia,
                'porcentaje': min(round(float(ganancia_mes) / float(objetivo.meta_ganancia) * 100, 1), 100) if objetivo.meta_ganancia > 0 else 0,
            },
            'tareas': {
                'actual': tareas_mes,
                'meta': objetivo.meta_tareas_completadas,
                'porcentaje': min(round(tareas_mes / objetivo.meta_tareas_completadas * 100, 1), 100) if objetivo.meta_tareas_completadas > 0 else 0,
            },
            'clientes': {
                'actual': clientes_mes,
                'meta': objetivo.meta_clientes_nuevos,
                'porcentaje': min(round(clientes_mes / objetivo.meta_clientes_nuevos * 100, 1), 100) if objetivo.meta_clientes_nuevos > 0 else 0,
            },
            'items': {
                'actual': items_mes,
                'meta': objetivo.meta_items_producidos,
                'porcentaje': min(round(items_mes / objetivo.meta_items_producidos * 100, 1), 100) if objetivo.meta_items_producidos > 0 else 0,
            },
        }
    
    # Notas activas
    notas_activas = NotaAnalisis.objects.filter(resuelta=False).order_by('-prioridad', '-creado_en')[:5]
    
    context = {
        'form_filtro': form_filtro,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        # KPIs Financieros
        'ingresos': ingresos,
        'costos': costos,
        'ganancia': ganancia,
        'margen': margen,
        'var_ingresos': var_ingresos,
        'var_ganancia': var_ganancia,
        'ticket_promedio': ticket_promedio,
        # KPIs Operativos
        'tareas_completadas': tareas_completadas,
        'tareas_total': tareas_total,
        'tasa_completacion': tasa_completacion,
        'var_tareas': var_tareas,
        'tiempo_promedio': tiempo_promedio,
        'tareas_vencidas': tareas_vencidas,
        'tasa_puntualidad': tasa_puntualidad,
        # KPIs Productividad
        'total_items_producidos': total_items_producidos,
        'total_horas_trabajo': round(total_horas_trabajo, 1),
        'productividad_hora': productividad_hora,
        'var_productividad': var_productividad,
        # KPIs Clientes
        'clientes_nuevos': clientes_nuevos,
        'total_clientes': total_clientes,
        'var_clientes': var_clientes,
        # Gráficas - JSON
        'labels_ingresos': json.dumps(labels_ingresos),
        'data_ingresos': json.dumps(data_ingresos),
        'data_costos_chart': json.dumps(data_costos_chart),
        'data_ganancia_chart': json.dumps(data_ganancia_chart),
        'estado_labels': json.dumps(estado_labels),
        'estado_data': json.dumps(estado_data),
        'estado_bg': json.dumps(estado_bg),
        'proc_labels': json.dumps(proc_labels),
        'proc_totals': json.dumps(proc_totals),
        'top_prod_labels': json.dumps(top_prod_labels),
        'top_prod_data': json.dumps(top_prod_data),
        # Objetivos
        'objetivo': objetivo,
        'progreso_objetivo': progreso_objetivo,
        # Notas
        'notas_activas': notas_activas,
    }
    return render(request, 'panelanalisis/dashboard.html', context)


# =============================================
# ANÁLISIS DE RENDIMIENTO POR TRABAJADOR
# =============================================

@login_required
def analisis_trabajadores(request):
    """Análisis detallado de rendimiento por trabajador"""
    fecha_desde, fecha_hasta = _obtener_rango_fechas(request)
    form_filtro = FiltroAnalisisForm(initial={
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta
    })
    
    trabajadores = Trabajador.objects.filter(activo=True)
    ranking = []
    
    for trabajador in trabajadores:
        registros = RegistroProductividad.objects.filter(
            trabajador=trabajador,
            fecha__gte=fecha_desde,
            fecha__lte=fecha_hasta
        )
        
        total_items = 0
        total_horas = 0
        dias_trabajados = registros.values('fecha').distinct().count()
        
        desglose = defaultdict(int)
        proc_fields = ['cortado', 'marcado_piezas', 'costura', 'armado', 
                       'instalacion', 'sillas_realizadas', 'tapizado_puertas', 'tapizado_techo']
        
        for r in registros:
            total_items += r.total_items
            inicio = datetime.combine(r.fecha, r.hora_inicio)
            fin = datetime.combine(r.fecha, r.hora_finalizacion)
            if fin < inicio:
                fin += timedelta(days=1)
            total_horas += (fin - inicio).seconds / 3600
            
            for f in proc_fields:
                desglose[f] += getattr(r, f, 0)
        
        productividad_hora = round(total_items / total_horas, 1) if total_horas > 0 else 0
        items_por_dia = round(total_items / dias_trabajados, 1) if dias_trabajados > 0 else 0
        
        # Mejor proceso
        mejor_proceso = max(desglose.items(), key=lambda x: x[1])[0] if desglose else 'N/A'
        proc_nombres = {
            'cortado': 'Cortado', 'marcado_piezas': 'Marcado',
            'costura': 'Costura', 'armado': 'Armado',
            'instalacion': 'Instalación', 'sillas_realizadas': 'Sillas',
            'tapizado_puertas': 'Tap. Puertas', 'tapizado_techo': 'Tap. Techo'
        }
        
        ranking.append({
            'trabajador': trabajador,
            'total_items': total_items,
            'total_horas': round(total_horas, 1),
            'dias_trabajados': dias_trabajados,
            'productividad_hora': productividad_hora,
            'items_por_dia': items_por_dia,
            'mejor_proceso': proc_nombres.get(mejor_proceso, mejor_proceso),
            'desglose': dict(desglose),
        })
    
    # Ordenar por productividad por hora (descendente)
    ranking.sort(key=lambda x: x['productividad_hora'], reverse=True)
    
    # Datos para gráfica comparativa
    chart_labels = [r['trabajador'].nombre for r in ranking]
    chart_items = [r['total_items'] for r in ranking]
    chart_prod = [r['productividad_hora'] for r in ranking]
    
    context = {
        'form_filtro': form_filtro,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'ranking': ranking,
        'chart_labels': json.dumps(chart_labels),
        'chart_items': json.dumps(chart_items),
        'chart_prod': json.dumps(chart_prod),
    }
    return render(request, 'panelanalisis/trabajadores.html', context)


# =============================================
# ANÁLISIS FINANCIERO DETALLADO
# =============================================

@solo_jefes
def analisis_financiero(request):
    """Análisis financiero detallado con tendencias"""
    fecha_desde, fecha_hasta = _obtener_rango_fechas(request)
    form_filtro = FiltroAnalisisForm(initial={
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta
    })
    
    entregas = ProductoTarea.objects.filter(
        fecha_registro__date__gte=fecha_desde,
        fecha_registro__date__lte=fecha_hasta
    ).select_related('producto', 'tarea')
    
    # Resumen general
    total_ingresos = Decimal('0')
    total_costos = Decimal('0')
    total_cantidad = 0
    
    for e in entregas:
        total_ingresos += e.total_venta
        total_costos += e.total_costo
        total_cantidad += e.cantidad
    
    total_ganancia = total_ingresos - total_costos
    margen_promedio = round(float(total_ganancia / total_ingresos * 100), 1) if total_ingresos > 0 else 0
    
    # Rentabilidad por categoría
    por_categoria = []
    categorias = CategoriaProducto.objects.all()
    for cat in categorias:
        entregas_cat = entregas.filter(producto__categoria=cat)
        if entregas_cat.exists():
            ing = sum(e.total_venta for e in entregas_cat)
            cos = sum(e.total_costo for e in entregas_cat)
            gan = ing - cos
            cant = sum(e.cantidad for e in entregas_cat)
            por_categoria.append({
                'nombre': cat.nombre,
                'ingresos': ing,
                'costos': cos,
                'ganancia': gan,
                'cantidad': cant,
                'margen': round(float(gan / ing * 100), 1) if ing > 0 else 0,
            })
    por_categoria.sort(key=lambda x: x['ganancia'], reverse=True)
    
    # Productos más rentables
    productos_rentabilidad = []
    productos_unicos = entregas.values('nombre_producto').distinct()
    for p in productos_unicos:
        entregas_prod = entregas.filter(nombre_producto=p['nombre_producto'])
        ing = sum(e.total_venta for e in entregas_prod)
        cos = sum(e.total_costo for e in entregas_prod)
        gan = ing - cos
        cant = sum(e.cantidad for e in entregas_prod)
        productos_rentabilidad.append({
            'nombre': p['nombre_producto'],
            'ingresos': ing,
            'costos': cos,
            'ganancia': gan,
            'cantidad': cant,
            'margen': round(float(gan / ing * 100), 1) if ing > 0 else 0,
        })
    productos_rentabilidad.sort(key=lambda x: float(x['ganancia']), reverse=True)
    
    # Análisis de cobros / saldos pendientes
    tareas_activas = TareaPlanificada.objects.filter(
        estado__in=['pendiente', 'en_proceso', 'completado']
    )
    total_facturado = Decimal('0')
    total_abonado = Decimal('0')
    for t in tareas_activas:
        total_facturado += t.precio_total
        total_abonado += t.monto_abonado
    saldo_pendiente = total_facturado - total_abonado
    tasa_cobro = round(float(total_abonado / total_facturado * 100), 1) if total_facturado > 0 else 0
    
    # Clientes morosos
    morosos = []
    for t in tareas_activas:
        saldo_t = t.saldo_pendiente
        if saldo_t > 0:
            morosos.append({
                'tarea': t,
                'saldo': saldo_t,
                'total': t.precio_total,
                'abonado': t.monto_abonado,
            })
    morosos.sort(key=lambda x: x['saldo'], reverse=True)
    
    # Datos para gráfica de categorías
    cat_labels = [c['nombre'] for c in por_categoria]
    cat_ingresos = [float(c['ingresos']) for c in por_categoria]
    cat_ganancia = [float(c['ganancia']) for c in por_categoria]
    
    context = {
        'form_filtro': form_filtro,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_ingresos': total_ingresos,
        'total_costos': total_costos,
        'total_ganancia': total_ganancia,
        'total_cantidad': total_cantidad,
        'margen_promedio': margen_promedio,
        'por_categoria': por_categoria,
        'productos_rentabilidad': productos_rentabilidad[:15],
        'total_facturado': total_facturado,
        'total_abonado': total_abonado,
        'saldo_pendiente': saldo_pendiente,
        'tasa_cobro': tasa_cobro,
        'morosos': morosos,
        'cat_labels': json.dumps(cat_labels),
        'cat_ingresos': json.dumps(cat_ingresos),
        'cat_ganancia': json.dumps(cat_ganancia),
    }
    return render(request, 'panelanalisis/financiero.html', context)


# =============================================
# OBJETIVOS MENSUALES
# =============================================

@login_required
def lista_objetivos(request):
    """Lista de objetivos mensuales"""
    objetivos = ObjetivoMensual.objects.all()
    usuario_es_jefe = request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.es_jefe)
    return render(request, 'panelanalisis/objetivos/lista.html', {
        'objetivos': objetivos,
        'es_jefe': usuario_es_jefe,
    })


@solo_jefes
def crear_objetivo(request):
    """Crear un nuevo objetivo mensual"""
    if request.method == 'POST':
        form = ObjetivoMensualForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.creado_por = request.user
            obj.save()
            messages.success(request, 'Objetivo mensual creado correctamente.')
            return redirect('analisis:lista_objetivos')
    else:
        form = ObjetivoMensualForm(initial={'mes': date.today().replace(day=1)})
    return render(request, 'panelanalisis/objetivos/crear.html', {'form': form})


@solo_jefes
def editar_objetivo(request, pk):
    """Editar un objetivo mensual"""
    objetivo = get_object_or_404(ObjetivoMensual, pk=pk)
    if request.method == 'POST':
        form = ObjetivoMensualForm(request.POST, instance=objetivo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Objetivo actualizado correctamente.')
            return redirect('analisis:lista_objetivos')
    else:
        form = ObjetivoMensualForm(instance=objetivo)
    return render(request, 'panelanalisis/objetivos/editar.html', {
        'form': form, 'objetivo': objetivo
    })


@solo_jefes
def eliminar_objetivo(request, pk):
    """Eliminar un objetivo mensual"""
    objetivo = get_object_or_404(ObjetivoMensual, pk=pk)
    if request.method == 'POST':
        objetivo.delete()
        messages.success(request, 'Objetivo eliminado correctamente.')
        return redirect('analisis:lista_objetivos')
    return render(request, 'panelanalisis/objetivos/eliminar.html', {'objetivo': objetivo})


# =============================================
# NOTAS DE ANÁLISIS
# =============================================

@login_required
def lista_notas(request):
    """Lista de notas de análisis"""
    notas = NotaAnalisis.objects.all()
    filtro = request.GET.get('filtro', 'activas')
    if filtro == 'activas':
        notas = notas.filter(resuelta=False)
    elif filtro == 'resueltas':
        notas = notas.filter(resuelta=True)
    
    usuario_es_jefe = request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.es_jefe)
    return render(request, 'panelanalisis/notas/lista.html', {
        'notas': notas,
        'filtro': filtro,
        'es_jefe': usuario_es_jefe,
    })


@login_required
def crear_nota(request):
    """Crear una nueva nota de análisis"""
    if request.method == 'POST':
        form = NotaAnalisisForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.creado_por = request.user
            nota.save()
            messages.success(request, 'Nota creada correctamente.')
            return redirect('analisis:lista_notas')
    else:
        form = NotaAnalisisForm()
    return render(request, 'panelanalisis/notas/crear.html', {'form': form})


@login_required
def resolver_nota(request, pk):
    """Marcar una nota como resuelta"""
    nota = get_object_or_404(NotaAnalisis, pk=pk)
    nota.resuelta = not nota.resuelta
    nota.save()
    estado = 'resuelta' if nota.resuelta else 'reabierta'
    messages.success(request, f'Nota marcada como {estado}.')
    return redirect('analisis:lista_notas')


@login_required
def eliminar_nota(request, pk):
    """Eliminar una nota"""
    nota = get_object_or_404(NotaAnalisis, pk=pk)
    if request.method == 'POST':
        nota.delete()
        messages.success(request, 'Nota eliminada correctamente.')
        return redirect('analisis:lista_notas')
    return render(request, 'panelanalisis/notas/eliminar.html', {'nota': nota})
