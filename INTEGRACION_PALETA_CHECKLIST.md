# 📋 CHECKLIST DE INTEGRACIÓN - PALETA DE LUJO

**Fecha de Creación:** 2024
**Estado:** Activo
**Prioridad:** Alta

---

## 🎯 Objetivo
Refactorizar todos los templates HTML de Tapicería Cuir para usar la paleta de lujo (#2B1B17) como sistema de diseño unificado.

---

## 📊 PROGRESO GENERAL

```
██████░░░░░░░░░░░░░░░░░░░░░░░ 20% (3/15 áreas completadas)
```

**Completados:** 3/15 | **En Progreso:** 0/15 | **Pendientes:** 12/15

---

## ✅ MÓDULOS COMPLETADOS

### 1. **Base de Diseño** ✅
- [x] `static/css/luxury-palette.css` - Sistema de variables CSS
- [x] `static/css/PALETTE_GUIDE.md` - Documentación de referencia
- [x] `templates/base.html` - Integración inicial de palette
- **Archivos:** 1 CSS + 1 Markdown + 1 Template
- **Estado:** LISTO PARA USAR

### 2. **Ejemplo Implementación** ✅
- [x] `templates/ejemplo_paleta.html` - Template de referencia
- **Propósito:** Mostrar correcto uso de colores y componentes
- **Estado:** DISPONIBLE PARA CONSULTA

### 3. **Dashboard Principal** ✅
- [x] Stat-cards con gradientes de lujo ✅
- [x] Page-header con palette ✅
- [x] Navigation styling ✅
- **Estado:** INTEGRADO EN BASE.HTML

---

## 🔄 MÓDULOS EN PROGRESO

(Ninguno actualmente - Aguardando definición de prioridades)

---

## 📝 MÓDULOS PENDIENTES

### PANEL ANÁLISIS (panelanalisis/)

#### 1. Dashboard
- [ ] [templates/panelanalisis/dashboard.html](templates/panelanalisis/dashboard.html)
  - **Elementos a refactorizar:**
    - Gráficos de productos
    - Tarjetas de resumen
    - Tablas de datos
  - **Colores a aplicar:**
    - Fondo: `var(--leather-dark)`
    - Acentos: `var(--gold-sand)`
    - Tablas: `var(--leather-dark)` header
  - **Prioridad:** ALTA (Dashboard principal)

#### 2. Financiero
- [ ] [templates/panelanalisis/financiero.html](templates/panelanalisis/financiero.html)
  - **Elementos a refactorizar:**
    - Cards de ingresos/gastos
    - Gráficos de tendencias financieras
    - Tablas de movimientos
  - **Colores sugeridos:**
    - Ingresos: `var(--success)` (#6B8E23)
    - Gastos: `var(--danger)` (#A0522D)
    - Neutra: `var(--gold-sand)`
  - **Prioridad:** ALTA (Datos financieros críticos)

#### 3. Trabajadores
- [ ] [templates/panelanalisis/trabajadores.html](templates/panelanalisis/trabajadores.html)
  - **Elementos a refactorizar:**
    - Cards de productividad
    - Gráficos KPI
    - Listado de trabajadores
  - **Prioridad:** MEDIA

---

### PANEL ESTÁNDARES (panelestandares/)

#### 1. Estándares
- [ ] [templates/panelestandares/...html](templates/panelestandares/)
  - **Elementos:** Cards, botones, tablas
  - **Prioridad:** MEDIA

---

### PANEL FINANZAS (panelfinanzas/)

#### 1. Gestión de Productos
- [ ] [templates/panelfinanzas/crear.html](templates/panelfinanzas/crear.html)
  - **Elementos a refactorizar:**
    - Inputs de formulario
    - Botones de acción
    - Botones de fecha/hora ⚠️
  - **Notas:** 
    - Incluye botón "Hoy" para fechas
    - Incluye botón "Actual" para horas
    - Verificar funcionalidad de botones
  - **Prioridad:** ALTA (Formulario crítico)

- [ ] [templates/panelfinanzas/editar.html](templates/panelfinanzas/editar.html)
  - **Similar a crear.html** - Mismo tratamiento
  - **Prioridad:** ALTA

#### 2. Lista de Productos
- [ ] Listado de productos
  - **Elementos:** Tabla con acciones
  - **Prioridad:** MEDIA

#### 3. Gastos
- [ ] Gestión de gastos
  - **Elementos:** Formularios, tablas
  - **Prioridad:** MEDIA

---

### PANEL TAREAS (paneltareas/)

#### 1. Crear Tarea
- [ ] [templates/paneltareas/crear.html](templates/paneltareas/crear.html)
  - **Elementos a refactorizar:**
    - Form inputs
    - Button "Hoy" ⚠️
    - Button "Actual" ⚠️
    - Input groups
  - **Prioridad:** ALTA (Formulario frecuente)

#### 2. Editar Tarea
- [ ] [templates/paneltareas/editar.html](templates/paneltareas/editar.html)
  - **Similar a crear** - Mismo tratamiento
  - **Prioridad:** ALTA

#### 3. Lista de Tareas
- [ ] Listado de tareas
  - **Elementos:** Kanban board (si existe), tabla
  - **Prioridad:** MEDIA

#### 4. Clientes
- [ ] Gestión de clientes
  - **Elementos:** Formularios, tabla de clientes
  - **Prioridad:** MEDIA

---

### PANEL PRODUCTIVIDAD (panelproductividad/)

#### 1. Registro de Productividad
- [ ] [templates/panelproductividad/crear.html](templates/panelproductividad/crear.html)
  - **Elementos a refactorizar:**
    - Form inputs
    - Dropdowns de tareas
    - Campos de tiempo
  - **Prioridad:** ALTA (Datos críticos)

#### 2. Listado/Dashboard Productividad
- [ ] Listado de registros
  - **Elementos:** Tabla, gráficos de rendimiento
  - **Prioridad:** MEDIA

#### 3. Vista Trabajador
- [ ] [templates/trabajador/...html](templates/trabajador/)
  - **Elementos:** Dashboard personalizado para workers
  - **Notas:** Verificar permisos (ya implementados)
  - **Prioridad:** MEDIA

---

### AUTENTICACIÓN & ADMIN

#### 1. Login
- [ ] [templates/login.html](templates/login.html)
  - **Elementos a refactorizar:**
    - Form de login
    - Inputs
    - Botón submit
  - **Notas:** 
    - Aplicar gradiente de lujo
    - Fondo: leather-dark
    - Forma: Elegante, minimalista
  - **Prioridad:** ALTA (Primera impresión)

#### 2. Home (Antes del Dashboard)
- [ ] [templates/home.html](templates/home.html)
  - **Elementos a refactorizar:**
    - Hero section
    - Cards de opciones
    - Botones de navegación
  - **Prioridad:** MEDIA

---

## 🛠️ INSTRUCCIONES PARA REFACTORIZACIÓN

### Paso 1: Preparación
```html
<!-- VERIFICAR que el template hereda de base.html -->
{% extends 'base.html' %}

<!-- VERIFICAR que luxury-palette.css está importado en base.html -->
<!-- (Ya implementado en base.html automaticamente) -->
```

### Paso 2: Reemplazar Colores
```css
/* ANTES - Hardcoded colors */
background-color: #2B1B17;
color: #B88A4D;
border: 1px solid #4A2C22;

/* DESPUÉS - CSS Variables */
background-color: var(--leather-dark);
color: var(--gold-sand);
border: 1px solid var(--leather-chocolate);
```

### Paso 3: Aplicar Clases Utilidad
```html
<!-- ANTES -->
<div style="color: #D4A373;">Texto en oro viejo</div>

<!-- DESPUÉS -->
<div class="text-secondary">Texto en oro viejo</div>
```

### Paso 4: Actualizar Componentes
- **Cards:** Hereda automáticamente estilos
- **Botones:** Usar clases `btn-primary`, `btn-secondary`, etc.
- **Inputs:** Enfoques automáticos con borde dorado
- **Tables:** Estilos aplicados automáticamente

### Paso 5: Testing
- [ ] Abrir en navegador
- [ ] Verificar colores se aplican correctamente
- [ ] Probar responsive en móvil
- [ ] Verificar contraste texto (WCAG AA)
- [ ] Probar funcionalidad de interactivos

---

## 📊 MATRIZ DE PRIORIDADES

### 🔴 CRÍTICA (Para completar PRIMERO)
1. **login.html** - Primera impresión del usuario
2. **panelfinanzas/crear.html** - Formulario frecuente (con botones de fecha/hora)
3. **panelfinanzas/editar.html** - Mismo que anterior
4. **paneltareas/crear.html** - Formulario crítico
5. **paneltareas/editar.html** - Mismo que anterior
6. **panelanalisis/dashboard.html** - Dashboard principal
7. **panelanalisis/financiero.html** - Datos financieros

### 🟡 MEDIA (Para después de CRÍTICA)
1. Listados de tareas
2. Listados de productos
3. Gestión de gastos
4. Dashboard de productividad
5. home.html
6. Vistas de trabajador

### 🟢 BAJA (Si queda tiempo)
1. Plantillas menores de admin
2. Vistas de error
3. Páginas informacionales

---

## 📋 PLANTILLA DE REFACTORIZACIÓN

```html
<!-- Copiar esta estructura para nuevos templates -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Nombre de Página{% endblock %}

{% block content %}

<!-- PAGE HEADER (Automático con palette) -->
<div class="page-header">
    <h1><i class="bi bi-[icono]"></i> Título</h1>
    <p>Descripción breve</p>
</div>

<!-- CONTENIDO PRINCIPAL -->
<div class="card">
    <div class="card-header">
        <i class="bi bi-[icono]" style="color: var(--gold-sand);"></i>
        Encabezado
    </div>
    <div class="card-body">
        <!-- Contenido aquí -->
    </div>
</div>

{% endblock %}
```

---

## 🔍 CHECKLIST DE VALIDACIÓN

Para cada template refactorizado, verificar:

- [ ] Usa `extends 'base.html'`
- [ ] Los colores hardcoded reemplazados por variables CSS
- [ ] Las clases utilidad aplicadas (text-gold, bg-leather, etc.)
- [ ] Los botones usan clases Bootstrap correctas
- [ ] Los inputs tienen clases `form-control` para estilos automáticos
- [ ] Las tablas heredan estilos de palette
- [ ] Cards tienen clase `card` para estilos automáticos
- [ ] El contraste de texto cumple WCAG AA
- [ ] Responsive en mobile (Bootstrap grid)
- [ ] Iconos Bootstrap cargados correctamente
- [ ] Sin errores en consola del navegador
- [ ] Botones interactivos funcionan correctamente

---

## 📈 MÉTRICAS DE PROGRESO

| Fecha | Completados | Pendientes | % Progreso |
|-------|-------------|-----------|-----------|
| Inicio | 3/15 | 12/15 | 20% |
| [Próxima] | | | |

---

## 📞 REFERENCIAS RÁPIDAS

- **Variables CSS:** Ver `static/css/luxury-palette.css`
- **Guía Completa:** Ver `static/css/PALETTE_GUIDE.md`
- **Ejemplo:** Ver `templates/ejemplo_paleta.html`
- **Base Template:** Ver `templates/base.html`

---

## 🎯 PRÓXIMA ACCIÓN

**Recomendado:** Empezar por refactorizar **login.html** (causa primera impresión) y luego los formularios de finanzas/tareas (altamente usados).

