#!/usr/bin/env python
import os
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoempresa.settings')
django.setup()

from paneltareas.models import TareaPlanificada, ProductoTarea
from panelproductividad.models import RegistroProductividad

# Mismo rango de fechas que usa el dashboard
hoy = date.today()
fecha_desde = hoy.replace(month=1, day=1)
fecha_hasta = hoy

print("=" * 60)
print("DEBUG: Cálculo de Margen y Tasa de Completación")
print("=" * 60)
print(f"\nPeríodo: {fecha_desde} hasta {fecha_hasta}\n")

# MARGEN DE GANANCIA
print("1️⃣ MARGEN DE GANANCIA:")
print("-" * 60)

entregas = ProductoTarea.objects.filter(
    fecha_registro__date__gte=fecha_desde,
    fecha_registro__date__lte=fecha_hasta
)

ingresos = Decimal('0')
costos = Decimal('0')
for e in entregas:
    ingresos += e.total_venta
    costos += e.total_costo

ganancia = ingresos - costos
margen = round((ganancia / ingresos * 100), 1) if ingresos > 0 else 0

print(f"   Ingresos totales: ${ingresos:.2f}")
print(f"   Costos totales: ${costos:.2f}")
print(f"   Ganancia: ${ganancia:.2f}")
print(f"   Margen: {margen}%")
print(f"   Cálculo: ({float(ganancia):.2f} / {float(ingresos):.2f}) * 100 = {margen}%")

# TASA DE COMPLETACIÓN
print("\n2️⃣ TASA DE COMPLETACIÓN:")
print("-" * 60)

tareas_periodo = TareaPlanificada.objects.filter(
    fecha_ingreso__gte=fecha_desde,
    fecha_ingreso__lte=fecha_hasta
)

tareas_completadas = tareas_periodo.filter(estado='completado').count()
tareas_total = tareas_periodo.count()
tasa_completacion = round((tareas_completadas / tareas_total * 100), 1) if tareas_total > 0 else 0

print(f"   Tareas completadas: {tareas_completadas}")
print(f"   Total de tareas: {tareas_total}")
print(f"   Tasa: {tasa_completacion}%")
print(f"   Cálculo: ({tareas_completadas} / {tareas_total}) * 100 = {tasa_completacion}%")

print("\n" + "=" * 60)
print(f"✓ Los valores generados son:")
print(f"  - margen = {margen}")
print(f"  - tasa_completacion = {tasa_completacion}")
print("=" * 60)
