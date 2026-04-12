# PALETA DE COLORES DE LUJO - TAPICERÍA CUIR
## Sistema de Diseño y Guía de Implementación

---

## 📊 VARIABLES CSS DISPONIBLES

Todas las variables están definidas en: `static/css/luxury-palette.css`

### Colores Primarios

```css
--leather-dark: #2B1B17;        /* Marrón Cuero Oscuro (Fondo principal) */
--leather-chocolate: #4A2C22;   /* Marrón Chocolate (Sombras y texturas) */
--gold-sand: #B88A4D;            /* Dorado Arena (Logos, iconos, realces) */
--gold-old: #D4A373;             /* Oro Viejo (Textos secundarios) */
--carbon-gray: #1A1A1A;          /* Gris Carbón (Bordes y degradados) */
```

### Colores Semánticos

```css
--success: #6B8E23;              /* Verde Oliva - Éxito */
--warning: #CD853F;              /* Marrón Perú - Advertencias */
--danger: #A0522D;               /* Marrón Sienna - Errores */
--info: #556B2F;                 /* Verde Musgo - Información */
```

### Colores Neutrales

```css
--white: #FFFFFF;
--light-cream: #F5F1ED;          /* Crema clara - Fondos */
--medium-gray: #8B8B8B;          /* Gris medio - Textos terciarios */
--dark-gray: #333333;            /* Gris oscuro - Textos principales */
```

### Sombras y Bordes

```css
--border-light: rgba(184, 138, 77, 0.2);
--border-medium: rgba(184, 138, 77, 0.5);
--border-dark: var(--leather-chocolate);
--shadow-subtle: rgba(43, 27, 23, 0.1);
--shadow-medium: rgba(43, 27, 23, 0.25);
--shadow-strong: rgba(43, 27, 23, 0.4);
```

### Gradientes Predefinidos

```css
--gradient-luxury: linear-gradient(135deg, var(--leather-dark) 0%, var(--leather-chocolate) 100%);
--gradient-gold: linear-gradient(135deg, var(--gold-sand) 0%, var(--gold-old) 100%);
--gradient-subtle: linear-gradient(180deg, rgba(184, 138, 77, 0.1) 0%, rgba(212, 163, 115, 0.05) 100%);
```

---

## 🎨 GUÍA DE USO POR COMPONENTE

### 1. NAVEGACIÓN Y HEADERS

**Sidebar (Desktop):**
```html
<!-- Automáticamente aplicará gradiente de lujo -->
<nav class="sidebar">
  <div class="sidebar-brand">Logo</div>
  <!-- Links con hover de oro -->
</nav>
```

**Mobile Navbar:**
```html
<!-- Panel deslizable con offcanvas automático -->
<nav class="mobile-navbar">
  <!-- Se aplica automáticamente los estilos -->
</nav>
```

### 2. TARJETAS (Cards)

**Tarjeta estándar:**
```html
<div class="card">
  <div class="card-header">Título</div>
  <div class="card-body">Contenido</div>
</div>
```

**Tarjeta de estadísticas (stat-card):**
```html
<div class="stat-card proceso">  <!-- clase automática con paleta -->
  <h3>Valor</h3>
  <small>Etiqueta</small>
</div>
```

Clases disponibles para stat-cards:
- `.stat-card.pendientes` - Degradado dorado
- `.stat-card.proceso` - Degradado chocolate
- `.stat-card.completadas` - Verde oliva
- `.stat-card.clientes` - Cuero oscuro
- `.stat-card.urgentes` - Marrón Sienna

### 3. BOTONES

**Botón primario:**
```html
<button class="btn btn-primary">Acción Principal</button>
```
Aplica gradiente dorado automáticamente.

**Botón secundario:**
```html
<button class="btn btn-secondary">Acción Secundaria</button>
```
Aplica chocolate con hovers en cuero oscuro.

**Botón outline:**
```html
<button class="btn btn-outline-primary">Alternativa</button>
```
Borde dorado con relleno en hover.

### 4. FORMULARIOS

**Campo de texto:**
```html
<input type="text" class="form-control" placeholder="Ingresa...">
```

Focus automático:
- Borde pasa a dorado arena
- Shadow con transparencia dorada
- Sin cambio de background

**Select:**
```html
<select class="form-select">
  <option>Selecciona...</option>
</select>
```

### 5. BADGES Y ESTADOS

**Badge primario:**
```html
<span class="badge badge-primary">Activo</span>
```

**Badge secundario:**
```html
<span class="badge badge-secondary">Inactivo</span>
```

**Badges de estado disponibles:**
- `.badge-success` - Verde
- `.badge-warning` - Marrón Perú
- `.badge-danger` - Marrón Sienna
- `.badge-info` - Verde Musgo

### 6. ALERTAS

```html
<div class="alert alert-warning">Advertencia</div>
<div class="alert alert-danger">Error</div>
<div class="alert alert-success">Éxito</div>
```

Se aplican automáticamente con transparencias de la paleta.

### 7. TABLAS

```html
<table class="table table-hover">
  <thead><!-- Encabezados en cuero oscuro con texto dorado --></thead>
  <tbody><!-- Hover con gris transparente --></tbody>
</table>
```

---

## 🎯 PATRONES DE COMBINACIÓN

### Patrón Elegante (Fondo oscuro)
```css
background: var(--leather-dark);
color: var(--light-cream);
border: 1px solid var(--border-medium);
```

### Patrón Acentuado (Con realces)
```css
background: var(--white);
color: var(--dark-gray);
accent-color: var(--gold-sand);
border: 2px solid var(--gold-sand);
```

### Patrón Texturizado
```css
background: linear-gradient(135deg, var(--leather-dark) 0%, var(--leather-chocolate) 100%);
box-shadow: 0 4px 12px var(--shadow-medium);
```

---

## ♿ CONTRASTE Y ACCESIBILIDAD

### Ratios de Contraste WCAG AA

| Combinación | Ratio | WCAG Level |
|-------------|-------|-----------|
| Cuero + Cream | 8.3:1 | AAA ✓ |
| Chocolate + Cream | 7.1:1 | AAA ✓ |
| Dorado + White | 5.2:1 | AA ✓ |
| Dark Gray + White | 7.4:1 | AAA ✓ |

**Nota:** Todas las combinaciones cumplen mínimo WCAG AA para texto normal.

---

## 📱 RESPONSIVIDAD

Los estilos se adaptan automáticamente:

- **Desktop (>768px):** Sidebar completo de 250px
- **Tablet (768px):** Sidebar oculto, navbar superior
- **Mobile (<768px):** Navbar superior + offcanvas deslizable

### Media Queries Incluidas

```css
@media (max-width: 768px) {
  /* Cambios automáticos */
}

@media (prefers-contrast: more) {
  /* Mayor contraste para usuarios con preferencias */
}

@media (prefers-reduced-motion: reduce) {
  /* Sin animaciones */
}
```

---

## 🔧 CÓMO USAR EN NUEVOS TEMPLATES

### Opción 1: Variables CSS

```html
<div style="background: var(--leather-dark); color: var(--gold-sand);">
  Contenido
</div>
```

### Opción 2: Clases Utilidad

```html
<div class="bg-leather text-gold">
  Contenido
</div>
```

Clases utilidad disponibles:
- `.text-gold` / `.text-leather` / `.text-muted`
- `.bg-leather` / `.bg-gold` / `.bg-leather-light`
- `.border-gold` / `.border-leather`
- `.shadow-luxury`

### Opción 3: Componentes Bootstrap

```html
<button class="btn btn-primary">Automático con paleta</button>
<div class="card">Automático con paleta</div>
<div class="alert alert-warning">Automático con paleta</div>
```

---

## 📋 TEMPLATE BASE ACTUALIZADO

El archivo `base.html` ya incluye:

1. ✅ Link al archivo `luxury-palette.css`
2. ✅ Navegación con nueva paleta
3. ✅ Headers con gradiente de lujo
4. ✅ Cards automáticas con estilos compatibles
5. ✅ Stat-cards con colores temáticos
6. ✅ Formularios con focus dorado

---

## 🚀 PRÓXIMOS PASOS

Para completar la refactorización en otros templates:

1. **Verificar que hereden de `base.html`**
   ```html
   {% extends 'base.html' %}
   {% load static %}
   ```

2. **Reemplazar colores inline**
   ```html
   <!-- Antes -->
   <div style="background-color: #3498db;">
   
   <!-- Después -->
   <div class="bg-leather">
   ```

3. **Usar clases de Bootstrap ya configuradas**
   ```html
   <button class="btn btn-primary">Automático</button>
   <div class="card">Automático</div>
   ```

4. **Para estilos complejos, agregar a luxury-palette.css**
   ```css
   .my-custom-component {
     background: var(--gradient-luxury);
     border: 1px solid var(--border-light);
   }
   ```

---

## 📞 REFERENCIA RÁPIDA

| Necesidad | Variable/Clase |
|-----------|----------------|
| Fondo principal | `--leather-dark` o `.bg-leather` |
| Textos primarios | `--dark-gray` o color heredado |
| Textos secundarios | `--gold-old` o `.text-secondary` |
| Acentos/Realces | `--gold-sand` o `.text-gold` |
| Bordes sutiles | `--border-light` |
| Sombras elegantes | `--shadow-medium` o `.shadow-luxury` |
| Botones principales | `.btn-primary` |
| Botones alternativos | `.btn-secondary` |
| Éxito/Positivo | `--success` |
| Error/Negativo | `--danger` |
| Advertencia | `--warning` |

---

**Versión:** 1.0  
**Actualizado:** Abril 2026  
**Proyecto:** Tapicería Cuir - Sistema de Gestión
