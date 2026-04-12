# 💰 GUÍA DE FORMATEO DE DINERO EN EL PROYECTO

## Descripción General

Se ha implementado un sistema completo de formateo de valores monetarios con separadores de miles en formato latino:
- **Formato**: `1.234.567,89` (punto para miles, coma para decimales)
- **Aplica automáticamente** a valores con más de 6 dígitos (≥ 1.000.000)
- **Disponible** en Django templates y JavaScript frontend

---

## 📋 FILTROS DJANGO (Templates)

### 1. Filtro `formato_dinero`
**Uso más flexible y recomendado**

```django
{{ valor|formato_dinero }}           <!-- 1.234.567 (sin decimales) -->
{{ valor|formato_dinero:0 }}         <!-- 1.234.567 (sin decimales) -->
{{ valor|formato_dinero:2 }}         <!-- 1.234.567,89 (con 2 decimales) -->
{{ precio_total|formato_dinero:2 }}  <!-- Ejemplo real -->
```

**En templates:**
```html
<h3>Precio Total: {{ tarea.precio_total|formato_dinero:2 }}</h3>
<p>Saldo: {{ tarea.saldo_pendiente|formato_dinero:0 }}</p>
<p>Abonado: {{ tarea.monto_abonado|formato_dinero:2 }}</p>
```

### 2. Filtro `formato_moneda`
**Alias de `formato_dinero` con 2 decimales por defecto**

```django
{{ valor|formato_moneda }}      <!-- Equivalente a formato_dinero:2 -->
{{ precio|formato_moneda:0 }}   <!-- Con decimales personalizados -->
```

### 3. Filtro `formato_precio`
**Alias para formatear sin decimales por defecto**

```django
{{ producto.precio|formato_precio }}    <!-- Sin decimales -->
{{ producto.precio|formato_precio:2 }}  <!-- Con 2 decimales -->
```

### 4. Filtro `es_grande`
**Verifica si un número tiene más de 6 dígitos**

```django
{% if monto|es_grande %}
    {{ monto|formato_dinero:2 }}  <!-- Solo formatea si es >= 1.000.000 -->
{% else %}
    {{ monto }}
{% endif %}
```

### ⚙️ Carga en template
Agrega esto al inicio de cualquier template que use los filtros:

```django
{% load money_format %}

<!-- Ahora puedes usar los filtros -->
{{ dinero|formato_dinero:2 }}
```

---

## 🟨 FUNCIONES JAVASCRIPT (Frontend)

Archivo: `static/js/format-dinero.js`

### 1. Función `formatoDinero(valor, decimales)`
**Formatea números en JavaScript**

```javascript
formatoDinero(1234567.89)      // "1.234.567"
formatoDinero(1234567.89, 2)   // "1.234.567,89"
formatoDinero(500000, 0)       // "500.000"
formatoDinero("1.234.567,89")  // "1.234.567,89"
```

**Uso en código:**
```javascript
const saldo = tarea.saldo_pendiente;
const formateado = formatoDinero(saldo, 2);
console.log(`Saldo: $${formateado}`);  // "Saldo: $1.234.567,89"
```

### 2. Función `formatoMoneda(valor, moneda, decimales)`
**Formatea con símbolo de moneda**

```javascript
formatoMoneda(1234567.89)              // "$ 1.234.567,89"
formatoMoneda(1234567.89, 'USD', 2)   // "USD 1.234.567,89"
formatoMoneda(500000, '€')             // "€ 500.000,00"
```

### 3. Función `parsearDinero(valor)`
**Convierte string formateado de vuelta a número**

```javascript
parsearDinero("1.234.567,89")  // 1234567.89
parsearDinero("500.000")       // 500000
parsearDinero("$ 1.234,50")    // 1234.50
```

### 4. Función `esGrande(valor, limite)`
**Verifica si un número tiene más de 6 dígitos**

```javascript
esGrande(1500000)      // true (>= 1.000.000)
esGrande(500000)       // false (< 1.000.000)
esGrande(2500000, 2000000)  // true (límite personalizado)
```

### 5. Función `formatearDineroEnDOM()`
**Automática: formatea todos los elementos con clase `money-format`**

```html
<!-- Uso automático en HTML -->
<span class="money-format" data-decimales="2">1234567.89</span>
<!-- Se convierte automáticamente a: 1.234.567,89 -->

<span class="money-format">5000</span>
<!-- Se convierte automáticamente a: 5.000 -->
```

---

## 📍 LUGARES DONDE YA ESTÁ IMPLEMENTADO

### ✅ Templates
- `templates/paneltareas/kanban.html` - Tabla Kanban (saldo pendiente)

### ✅ JavaScript
- `static/js/format-dinero.js` - Todas las funciones disponibles

### ⚠️ PARA IMPLEMENTAR EN

Las siguientes áreas pueden beneficiarse del formateo:

#### Templates
```
- templates/home.html: saldo_total_pendiente, total_gastos_mes
- templates/paneltareas/detalle.html: precio_total, monto_abonado
- templates/panelfinanzas/*.html: todos los totales
- templates/panelanalisis/*.html: totales financieros
```

#### Ejemplos de uso:
```django
{% load money_format %}

<!-- home.html -->
<h3>{{ saldo_total_pendiente|formato_dinero:2 }}</h3>
<p>Gastos: {{ total_gastos_mes|formato_dinero:2 }}</p>

<!-- detalle.html -->
<strong>Precio: {{ tarea.precio_total|formato_dinero:2 }}</strong>
<strong>Abonado: {{ tarea.monto_abonado|formato_dinero:2 }}</strong>
```

#### Views (Python)
Para valores que se calculan en la vista y se pasan al template:
```python
context = {
    'saldo_total': Decimal('1234567.89'),
    # El filtro se aplica en el template, no en la vista
}
```

---

## 🎨 CONVENCIONES Y FORMATO

### Formato Elegido: Latino
- ✅ **Separadores de miles**: Punto (`.`)
- ✅ **Separador decimal**: Coma (`,`)
- ✅ **Ejemplo**: `1.234.567,89`
- ✅ **Países**: España, Latinoamérica, etc.

### Regla de los 6 Dígitos
- Aplica formato si el número tiene **≥ 7 dígitos** en la parte entera
- Ejemplo: `1.000.000` (1 millón) ← APLICA
- Ejemplo: `999.999` ← NO APLICA

---

## 🔧 PERSONALIZACIÓN

### Cambiar formato global
Edita `static/js/format-dinero.js`:

```javascript
// Línea ~50: cambiar punto por otro separador
parteEntera = parteEntera.replace(/\B(?=(\d{3})+(?!\d))/g, '.');  // Cambiar '.' aquí

// Línea ~55: cambiar coma por otro decimal
return parteEntera + ',' + parteDecimal;  // Cambiar ',' aquí
```

### Cambiar decimales por defecto
En templates:

```django
{# Por defecto 0 decimales #}
{{ valor|formato_dinero }}

{# Personalizar decimales #}
{{ valor|formato_dinero:3 }}
```

---

## ✨ EJEMPLOS COMPLETOS

### Ejemplo 1: Dashboard con totales
```django
{% load money_format %}

<div class="card">
    <h3>Resumen Financiero</h3>
    <ul>
        <li>Ingresos Esperados: <strong>{{ ingresos_esperados|formato_dinero:2 }}</strong></li>
        <li>Gastos del Mes: <strong>{{ total_gastos_mes|formato_dinero:2 }}</strong></li>
        <li>Saldo Pendiente: <strong>{{ saldo_total_pendiente|formato_dinero:2 }}</strong></li>
    </ul>
</div>
```

### Ejemplo 2: Tabla de productos
```django
{% load money_format %}

<table>
    {% for producto in productos %}
    <tr>
        <td>{{ producto.nombre }}</td>
        <td>{{ producto.precio_costo|formato_dinero:2 }}</td>
        <td>{{ producto.precio_venta|formato_dinero:2 }}</td>
        <td>{{ producto.ganancia|formato_dinero:2 }}</td>
    </tr>
    {% endfor %}
</table>
```

### Ejemplo 3: JavaScript y dinamicidad
```javascript
// En un script
const tareas = [
    { id: 1, precio: 1234567.89, abonado: 567890.45 },
    { id: 2, precio: 500000, abonado: 250000 }
];

tareas.forEach(tarea => {
    console.log(`Tarea ${tarea.id}:`);
    console.log(`  Precio: ${formatoDinero(tarea.precio, 2)}`);
    console.log(`  Abonado: ${formatoDinero(tarea.abonado, 2)}`);
});

// Resultado:
// Tarea 1:
//   Precio: 1.234.567,89
//   Abonado: 567.890,45
// Tarea 2:
//   Precio: 500.000,00
//   Abonado: 250.000,00
```

---

## 📊 RESUMEN DE ARCHIVOS AÑADIDOS

| Archivo | Propósito |
|---------|-----------|
| `paneltareas/templatetags/money_format.py` | Filtros Django personalizados |
| `paneltareas/templatetags/__init__.py` | Inicializador de módulo |
| `static/js/format-dinero.js` | Funciones JavaScript de formateo |
| `FORMATO_DINERO_GUIA.md` | Esta guía (documentación) |

---

## 🚀 PRÓXIMOS PASOS

1. **Aplicar filtros** a todos los templates del proyecto que muestren dinero
2. **Testar** valores grandes (>1.000.000) para verificar formato
3. **Integrar** en reportes y exportaciones PDF/Excel
4. **Considerar** símbolos de moneda si es necesario

---

**Última actualización**: Abril 2026
**Formato**: Latino (1.234.567,89)
**Precisión**: Hasta 2 decimales (configurable)
