#!/usr/bin/env python
import os
import sys
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoempresa.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

# Now test the imports and logic
from datetime import date, timedelta
from decimal import Decimal
from paneltareas.models import TareaPlanificada
from panelproductividad.models import RegistroProductividad, Trabajador
from panelfinanzas.models import Gasto
from django.db.models import Sum

hoy = date.today()
print(f"Fecha hoy: {hoy}")

# Test Cobranza
print("\n=== TESTING COBRANZA ===")
tareas_completadas = TareaPlanificada.objects.filter(estado='completada')
print(f"Tareas completadas: {tareas_completadas.count()}")

alertas_cobranza = []
saldo_total_pendiente = Decimal('0')
for tarea in tareas_completadas[:3]:
    print(f"  Tarea: {tarea.nombre_cliente}, Estado: {tarea.estado}, Saldo: {tarea.saldo_pendiente}")
    if tarea.saldo_pendiente > 0:
        saldo_total_pendiente += tarea.saldo_pendiente
        alertas_cobranza.append({'cliente': tarea.nombre_cliente, 'saldo': tarea.saldo_pendiente})

print(f"Saldo total pendiente: {saldo_total_pendiente}")
print(f"Alertas cobranza: {len(alertas_cobranza)}")

# Test Gastos
print("\n=== TESTING GASTOS ===")
primer_dia_mes = hoy.replace(day=1)
ultimo_dia_mes = (primer_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

gastos_mes = Gasto.objects.filter(
    fecha__gte=primer_dia_mes,
    fecha__lte=ultimo_dia_mes
)
print(f"Gastos este mes: {gastos_mes.count()}")
total_gastos_mes = sum(g.monto for g in gastos_mes)
print(f"Total gastos: {total_gastos_mes}")

gastos_por_categoria = gastos_mes.values('categoria').annotate(total=Sum('monto')).order_by('-total')
print(f"Categorías de gastos: {list(gastos_por_categoria)}")

# Test Tareas Críticas
print("\n=== TESTING TAREAS CRÍTICAS ===")
tareas_criticas = TareaPlanificada.objects.filter(
    estado__in=['pendiente', 'en_proceso'],
    fecha_entrega__lte=hoy + timedelta(days=7)
).order_by('fecha_entrega')[:5]
print(f"Tareas críticas: {tareas_criticas.count()}")
for tarea in tareas_criticas:
    dias_restantes = (tarea.fecha_entrega - hoy).days
    print(f"  - {tarea.nombre_cliente}: {dias_restantes} días")

# Test Trabajadores sin registrar
print("\n=== TESTING TRABAJADORES SIN REGISTRAR ===")
todos_trabajadores = Trabajador.objects.filter(activo=True)
registrados_hoy = RegistroProductividad.objects.filter(fecha=hoy).values('trabajador_id').distinct()
registrados_hoy_ids = [r['trabajador_id'] for r in registrados_hoy]
trabajadores_sin_registrar = todos_trabajadores.exclude(id__in=registrados_hoy_ids)
print(f"Total trabajadores activos: {todos_trabajadores.count()}")
print(f"Registrados hoy: {len(registrados_hoy_ids)}")
print(f"Sin registrar: {trabajadores_sin_registrar.count()}")
for worker in trabajadores_sin_registrar[:3]:
    print(f"  - {worker.nombre}")

print("\nAll tests completed successfully!")
