# 📊 Tablero Kanban - Documentación Completa

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Endpoints API](#endpoints-api)
4. [Integración con Django](#integración-con-django)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Características](#características)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Descripción General

El Tablero Kanban es una solución completa que integra con el módulo `paneltareas` (llamado 'tareas' en URLs) para visualizar y organizar tareas por su estado mediante arrastrar y soltar (drag-and-drop).

### Estados Soportados:
- **Pendiente** (🟨 Amarillo)
- **En Proceso** (🔵 Azul)
- **Completado** (🟢 Verde)
- **Cancelado** (🔴 Rojo)

---

## 📁 Estructura de Archivos

```
proyectoempresa/
├── paneltareas/
│   ├── urls.py                      # ✏️ MODIFICADO - Nuevas rutas Kanban
│   ├── views_kanban.py              # ✨ NUEVO - Vistas API del Kanban
│   └── models.py                    # (Sin cambios necesarios)
│
└── templates/paneltareas/
    └── kanban.html                  # ✨ NUEVO - Template del Kanban
```

---

## 🔌 Endpoints API

### 1. **GET /tareas/kanban/**
Renderiza la página del tablero Kanban (HTML).

```bash
GET /tareas/kanban/
```

**Respuesta:** Template HTML del tablero Kanban

---

### 2. **GET /tareas/api/kanban/tareas/**
Obtiene todas las tareas agrupadas por estado en formato JSON.

**URL:**
```
/tareas/api/kanban/tareas/
```

**Parámetros (Query String):**
- `filtro_cliente` (string, opcional): Filtrar por nombre de cliente
- `filtro_placa` (string, opcional): Filtrar por placa del vehículo
- `filtro_prioridad` (string, opcional): Filtrar por prioridad (baja|media|alta|urgente)

**Ejemplo de solicitud:**
```bash
curl -X GET "http://localhost:8000/tareas/api/kanban/tareas/?filtro_cliente=Juan&filtro_prioridad=urgente" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Respuesta esperada (200 OK):**
```json
{
  "success": true,
  "data": {
    "pendiente": [
      {
        "id": 1,
        "cliente": "Juan García",
        "placa": "ABC-123",
        "descripcion": "Tapizado de asiento delantero...",
        "fecha_entrega": "15/04/2026",
        "dias_restantes": 4,
        "urgencia_visual": "proxima",
        "prioridad": "alta",
        "color_prioridad": "#e67e22",
        "estado": "pendiente",
        "saldo_pendiente": 250.50,
        "precio_total": 1000.00,
        "monto_abonado": 750.00,
        "porcentaje_pago": 75,
        "creado_por": "Carlos"
      }
    ],
    "en_proceso": [...],
    "completado": [...],
    "cancelado": [...]
  },
  "stats": {
    "total": 25,
    "pendiente": 8,
    "en_proceso": 5,
    "completado": 10,
    "cancelado": 2
  }
}
```

---

### 3. **POST /tareas/api/kanban/tareas/<tarea_id>/estado/**
Actualiza el estado de una tarea (usado en drag-and-drop).

**URL:**
```
/tareas/api/kanban/tareas/{tarea_id}/estado/
```

**Ejemplo:**
```
/tareas/api/kanban/tareas/42/estado/
```

**Body (JSON):**
```json
{
  "nuevo_estado": "en_proceso"
}
```

**Ejemplo completo con curl:**
```bash
curl -X POST "http://localhost:8000/tareas/api/kanban/tareas/42/estado/" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "nuevo_estado": "en_proceso"
  }'
```

**Respuesta esperada (200 OK):**
```json
{
  "success": true,
  "message": "Tarea actualizada a estado: en_proceso",
  "tarea": {
    "id": 42,
    "cliente": "María Pérez",
    "placa": "XYZ-789",
    "descripcion": "Cambio de llantas...",
    "fecha_entrega": "12/04/2026",
    "dias_restantes": 1,
    "urgencia_visual": "hoy",
    "prioridad": "urgente",
    "color_prioridad": "#e74c3c",
    "estado": "en_proceso",
    "saldo_pendiente": 100.00,
    "precio_total": 500.00,
    "monto_abonado": 400.00,
    "porcentaje_pago": 80,
    "creado_por": "Laura"
  }
}
```

**Errores posibles:**

```json
{
  "success": false,
  "error": "Tarea con ID 999 no encontrada"
}
```

---

### 4. **POST /tareas/api/kanban/reordenar/**
Reordena múltiples tareas (útil para sincronización).

**URL:**
```
/tareas/api/kanban/reordenar/
```

**Body (JSON):**
```json
{
  "tareas": [
    {
      "id": 1,
      "estado": "en_proceso",
      "orden": 1
    },
    {
      "id": 2,
      "estado": "en_proceso",
      "orden": 2
    },
    {
      "id": 5,
      "estado": "completado",
      "orden": 1
    }
  ]
}
```

**Respuesta esperada (200 OK):**
```json
{
  "success": true,
  "message": "3 tareas reordenadas"
}
```

---

## ⚙️ Integración con Django

### Paso 1: Verificar que los archivos estén en su lugar

✅ `proyectoempresa/paneltareas/views_kanban.py` - Nuevo archivo
✅ `proyectoempresa/templates/paneltareas/kanban.html` - Nuevo archivo
✅ `proyectoempresa/paneltareas/urls.py` - Modificado

### Paso 2: Verificar las URLs

En `proyectoempresa/paneltareas/urls.py` deben estar presentes:

```python
from . import views_kanban

urlpatterns = [
    # ... URLs existentes ...
    
    # Kanban Board
    path('kanban/', views_kanban.kanban_board, name='kanban'),
    path('api/kanban/tareas/', views_kanban.get_tareas_kanban, name='api_get_tareas_kanban'),
    path('api/kanban/tareas/<int:tarea_id>/estado/', views_kanban.actualizar_estado_tarea, name='api_actualizar_estado_tarea'),
    path('api/kanban/reordenar/', views_kanban.reordenar_tareas, name='api_reordenar_tareas'),
]
```

### Paso 3: Verificar que el modelo TareaPlanificada tiene los campos necesarios

Abre `proyectoempresa/paneltareas/models.py` y verifica que el modelo tenga:

```python
class TareaPlanificada(models.Model):
    # ... otros campos ...
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado'),
        ],
        default='pendiente'
    )
    # ... más campos ...
```

✅ El modelo ya tiene estos campos. **No hay cambios necesarios**.

### Paso 4: Migrar si es necesario

```bash
cd proyectoempresa
python manage.py makemigrations
python manage.py migrate
```

*(Probablemente no haya migraciones nuevas, pero ejecuta para estar seguro)*

### Paso 5: Reiniciar el servidor Django

```bash
python manage.py runserver
```

### Paso 6: Acceder al Kanban

Abre en el navegador:
```
http://localhost:8000/tareas/kanban/
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Cargar tareas con JavaScript vanilla

```javascript
// Obtener CSRF token
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// Fetch tareas
fetch('/tareas/api/kanban/tareas/')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('Tareas por estado:', data.data);
      console.log('Estadísticas:', data.stats);
    }
  });
```

### Ejemplo 2: Mover una tarea con fetch

```javascript
const tareaId = 42;
const nuevoEstado = 'completado';
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

fetch(`/tareas/api/kanban/tareas/${tareaId}/estado/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken,
  },
  body: JSON.stringify({
    nuevo_estado: nuevoEstado
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('✅ Tarea actualizada:', data.message);
    console.log('Datos actualizados:', data.tarea);
  } else {
    console.error('❌ Error:', data.error);
  }
});
```

### Ejemplo 3: Filtrar tareas

```javascript
// Filtrar por cliente y prioridad
const params = new URLSearchParams({
  'filtro_cliente': 'Juan',
  'filtro_prioridad': 'urgente'
});

fetch(`/tareas/api/kanban/tareas/?${params.toString()}`)
  .then(response => response.json())
  .then(data => {
    console.log('Tareas filtradas:', data.data);
  });
```

### Ejemplo 4: Usar con jQuery (si lo tienes en el proyecto)

```javascript
$.ajax({
  url: '/tareas/api/kanban/tareas/',
  type: 'GET',
  data: {
    'filtro_cliente': 'Juan García',
    'filtro_prioridad': 'alta'
  },
  success: function(data) {
    if (data.success) {
      console.log('Tareas:', data.data);
      console.log('Stats:', data.stats);
    }
  }
});
```

### Ejemplo 5: Reordenar múltiples tareas

```javascript
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

const ordenamiento = {
  'tareas': [
    {'id': 1, 'estado': 'pendiente', 'orden': 1},
    {'id': 2, 'estado': 'pendiente', 'orden': 2},
    {'id': 5, 'estado': 'completado', 'orden': 1},
  ]
};

fetch('/tareas/api/kanban/reordenar/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken,
  },
  body: JSON.stringify(ordenamiento)
})
.then(response => response.json())
.then(data => {
  console.log(data.message);
});
```

---

## ✨ Características

### 🎨 Diseño
- ✅ 4 columnas de estado con colores armoniosos
- ✅ Tarjetas modernas con sombras y transiciones
- ✅ Diseño responsive (funciona en móvil)
- ✅ Indicadores visuales de urgencia
- ✅ Barras de progreso de pago

### 🚀 Funcionalidad
- ✅ Drag-and-drop entre columnas (SortableJS)
- ✅ Filtros por cliente, placa y prioridad
- ✅ Estadísticas en tiempo real
- ✅ Validación y manejo de errores
- ✅ Logging para debugging

### 🔒 Seguridad
- ✅ Requiere autenticación (`@login_required`)
- ✅ CSRF protection en POST requests
- ✅ Decorador `@solo_jefes` (opcional, puedes agregarlo)

### ⚡ Performance
- ✅ Lazy loading de tareas
- ✅ API optimizada con `select_related`
- ✅ Ordenamiento por fecha de entrega
- ✅ Caché posible (implementable)

---

## 🔧 Solución de Problemas

### Problema: "Módulo 'views_kanban' no encontrado"

**Solución:**
```bash
# Asegúrate de que el archivo views_kanban.py existe en la carpeta paneltareas
ls proyectoempresa/paneltareas/views_kanban.py

# Si no existe, el archivo no fue creado correctamente
```

---

### Problema: "No se puede arrastrar tareas"

**Solución:**
```javascript
// Verifica que SortableJS cargó correctamente
console.log(window.Sortable); // Debe mostrar el objeto Sortable

// Si es undefined, la librería no se cargó
// Verifica tu conexión a CDN
```

---

### Problema: "Error 403: CSRF token missing"

**Solución:**
```html
<!-- Asegúrate de que el CSRF token está disponible -->
<form method="post">
    {% csrf_token %}  <!-- Esto debe estar en base.html -->
</form>
```

O en JavaScript:
```javascript
// Obtener CSRF token correctamente
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
if (!csrfToken) {
    console.error('CSRF token no encontrado');
}
```

---

### Problema: Las tareas no se actualizan después de mover

**Solución:**
```javascript
// El código JavaScript refresca automáticamente después de 500ms
// Si no funciona, verifica la consola del navegador para errores

// Fuerza una recarga manual
location.reload();
```

---

### Problema: Tareas no aparecen en el Kanban

**Solución:**
```python
# Verifica que el modelo tiene datos
from paneltareas.models import TareaPlanificada
print(TareaPlanificada.objects.count())  # Debe ser > 0

# Verifica que tienes permisos
# El usuario debe estar autenticado (@login_required)
```

---

## 📱 Interfaz de Usuario

### Filtros disponibles:
1. **Buscar Cliente** - Filtro de texto libre
2. **Buscar Placa** - Filtro de texto libre
3. **Prioridad** - Dropdown (Baja, Media, Alta, Urgente)
4. **Botón Aplicar** - Ejecuta los filtros

### Indicadores en tarjetas:
- 🔴 **Borde izquierdo coloreado** - Indica prioridad
- ⚠️ **Badges de urgencia** - Muestra vencidas/hoy/próximas
- 📊 **Barra de progreso** - Porcentaje de pago
- 💰 **Saldo pendiente** - Dinero faltante por cobrar

---

## 🚀 Mejoras Futuras

Puedes implementar estas características opcionales:

1. **Historial de Cambios**
   ```python
   # Crear modelo para registrar cambios de estado
   class CambioEstadoLog(models.Model):
       tarea = ForeignKey(TareaPlanificada)
       estado_anterior = CharField()
       estado_nuevo = CharField()
       realizado_por = ForeignKey(User)
       fecha = DateTimeField(auto_now_add=True)
   ```

2. **Notificaciones en Tiempo Real**
   - Usar Django Channels
   - WebSockets para actualizar tablero automáticamente

3. **Exportar a Excel**
   ```python
   # Vista para exportar tareas a formato Excel
   def exportar_tareas_excel(request):
       # Implementación con openpyxl
   ```

4. **Calendario con Kanban**
   - Integrar FullCalendar.js
   - Vista alternativa calendario + tareas

5. **Estadísticas Avanzadas**
   - Gráficos de velocidad (velocity charts)
   - Burndown charts
   - Tiempo promedio por estado

---

## 📞 Soporte

Si tienes problemas:

1. Revisa la consola del navegador (F12)
2. Revisa los logs de Django (`console.log`)
3. Verifica que todos los archivos estén en su lugar
4. Comprueba que las URLs estén registradas correctamente
5. Asegúrate de tener autenticación activa

---

## 📜 Licencia

Este código es parte del proyecto Django para gestión de tareas de la tapicería. 
Úsalo libremente dentro del proyecto.

---

**Documento generado:** Abril 2026
**Última actualización:** 11/04/2026
