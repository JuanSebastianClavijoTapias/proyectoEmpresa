# 🚀 GUÍA DE INTEGRACIÓN RÁPIDA - TABLERO KANBAN

## ✅ Checklist de Implementación

Esta guía te ayudará a integrar el Tablero Kanban en tu proyecto Django en **menos de 5 minutos**.

---

## 📝 Paso 1: Verificar que los archivos están en lugar

```bash
# Navega a la carpeta del proyecto
cd proyectoempresa

# Verifica que existan estos archivos:
ls paneltareas/views_kanban.py              # ✅ Nuevo
ls templates/paneltareas/kanban.html        # ✅ Nuevo
grep 'views_kanban' paneltareas/urls.py     # ✅ Modificado
```

**Si alguno falta, contacta al desarrollador.**

---

## 🔗 Paso 2: Verificar las URLs

Abre `paneltareas/urls.py` y asegúrate de que contenga esto:

```python
from django.urls import path
from . import views
from . import views_kanban  # ← Debe estar aquí

app_name = 'tareas'

urlpatterns = [
    # URLs existentes...
    
    # Kanban Board (agregar estas líneas)
    path('kanban/', views_kanban.kanban_board, name='kanban'),
    path('api/kanban/tareas/', views_kanban.get_tareas_kanban, name='api_get_tareas_kanban'),
    path('api/kanban/tareas/<int:tarea_id>/estado/', views_kanban.actualizar_estado_tarea, name='api_actualizar_estado_tarea'),
    path('api/kanban/reordenar/', views_kanban.reordenar_tareas, name='api_reordenar_tareas'),
]
```

✅ **Si está así, perfecto. Si no, cópialo tal cual.**

---

## 🗄️ Paso 3: Verificar el Modelo

Abre `paneltareas/models.py` y busca la clase `TareaPlanificada`.

Verifica que tenga este campo:

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
```

✅ **Si el campo existe, no necesitas hacer nada.**

---

## 🔄 Paso 4: Preparar la Base de Datos

```bash
# Ejecuta migraciones (por si acaso)
python manage.py migrate paneltareas

# Verifica que la BD tiene datos
python manage.py shell
>>> from paneltareas.models import TareaPlanificada
>>> TareaPlanificada.objects.count()
5  # Debería mostrar un número > 0
>>> exit()
```

---

## 🖥️ Paso 5: Iniciar el Servidor

```bash
python manage.py runserver
```

---

## 🌐 Paso 6: Acceder al Kanban

Abre tu navegador y ve a:

```
http://localhost:8000/tareas/kanban/
```

**Deberías ver:**
- 4 columnas (Pendiente, En Proceso, Completado, Cancelado)
- Tus tareas distribuidas por estado
- Barra de filtros en la parte superior
- Tarjetas arrastrables

✅ **¡Listo! El Kanban está funcional.**

---

## 🧪 Paso 7: Probar Funcionalidad

### Prueba 1: Cargar tareas
```
✅ Las tareas aparecen en sus columnas respectivas
```

### Prueba 2: Arrastrar una tarea
```
✅ Arrastra una tarea de una columna a otra
✅ Debe moverse sin refrescar la página
✅ Debe verse un mensaje de éxito en la esquina
```

### Prueba 3: Filtrar por cliente
```
1. Escribe un nombre en "Filtrar por Cliente"
2. Haz clic en "Aplicar Filtros"
✅ Solo aparecen tareas de ese cliente
```

### Prueba 4: Verificar estadísticas
```
✅ Los números arriba deben coincidir con las tareas mostradas
✅ Al mover una tarea, los números se actualizan
```

---

## 📊 Estructura de la Respuesta API

Cuando haces una petición a `/tareas/api/kanban/tareas/`, recibes esto:

```json
{
  "success": true,
  "data": {
    "pendiente": [
      {
        "id": 1,
        "cliente": "Juan García",
        "placa": "ABC-123",
        "descripcion": "Tapizado de asientos...",
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

## 🐛 Solución de Problemas Comunes

### ❌ Error: "No module named views_kanban"

**Solución:**
```bash
# Verifica que el archivo existe
ls paneltareas/views_kanban.py

# Verifica que la carpeta tiene __init__.py
ls paneltareas/__init__.py

# Si no existe, crea uno vacío
touch paneltareas/__init__.py
```

---

### ❌ Error: "404 - Page not found"

**Solución:**
```bash
# Verifica que la URL está registrada correctamente
grep -n "kanban" paneltareas/urls.py

# Si no aparece, checa que copiaste las URLs correctamente
```

---

### ❌ Error: "Las tareas no aparecen"

**Solución:**
```bash
# Verifica que tienes datos en la BD
python manage.py shell
>>> from paneltareas.models import TareaPlanificada
>>> TareaPlanificada.objects.count()
0  # Si es 0, crea algunas tareas de prueba
>>> exit()
```

---

### ❌ Error: "No se puede arrastrar tareas"

**Solución:**

1. Abre la consola del navegador (F12)
2. Busca errores en la pestaña "Console"
3. Verifica que SortableJS esté cargando:
   ```javascript
   console.log(window.Sortable);  // Debe mostrar el objeto
   ```

---

## 🎯 Funcionalidades Implementadas

- ✅ Drag-and-drop entre columnas
- ✅ Filtros por cliente, placa, prioridad
- ✅ Estadísticas en tiempo real
- ✅ Indicadores de urgencia (vencida, hoy, próxima)
- ✅ Barra de progreso de pago
- ✅ Diseño responsive
- ✅ Validación de estados
- ✅ Logging de cambios
- ✅ Manejo de errores

---

## 📚 Recursos Adicionales

### Documentation
- `KANBAN_DOCUMENTATION.md` - Documentación completa
- `ejemplos_kanban_api.py` - Ejemplos de consumo API
- `kanban_security_config.py` - Configuración avanzada

### API Endpoints
```
GET  /tareas/kanban/                              # Página principal
GET  /tareas/api/kanban/tareas/                   # Obtener tareas
POST /tareas/api/kanban/tareas/<id>/estado/       # Cambiar estado
POST /tareas/api/kanban/reordenar/                # Reordenar
```

---

## 🔐 Seguridad Implementada

- ✅ `@login_required` en todas las vistas
- ✅ CSRF protection en POST requests
- ✅ Validación de entrada (JSON)
- ✅ Manejo de excepciones
- ✅ Logging de auditoría

---

## 📈 Estadísticas del Sistema

El Kanban incluye:
- Contadores de tareas por estado
- Indicador de urgencia visual
- Barras de progreso de pago
- Cálculo automático de días restantes

---

## 🎨 Personalización

### Cambiar Colores

Edita `templates/paneltareas/kanban.html` y busca:

```html
<!-- Columna: Pendiente -->
<div class="column-header" style="background: linear-gradient(135deg, #f39c12 0%, #d68910 100%);">
```

Cambia los colores hex (#f39c12, #d68910) por los que quieras.

### Cambiar Ancho de Columnas

En el CSS del mismo archivo:

```css
.kanban-board {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));  /* Cambiar 350px */
}
```

---

## 🚀 Próximos Pasos

Una vez que el Kanban esté funcionando, puedes:

1. **Agregar a menú principal:**
   - Edita `templates/base.html`
   - Agrega un link a `/tareas/kanban/`

2. **Mejorar dashboard:**
   - Integra gráficos con Chart.js
   - Muestra KPIs del Kanban

3. **Notificaciones:**
   - Integra Django Channels
   - Actualiza tareas en tiempo real

4. **Exportar datos:**
   - Agrega botón para exportar a Excel
   - Genera reportes PDF

---

## 📞 Ayuda y Soporte

Si tienes problemas:

1. **Revisa la consola del navegador** (F12)
2. **Revisa los logs de Django** en terminal
3. **Consulta la documentación** (KANBAN_DOCUMENTATION.md)
4. **Revisa ejemplos** (ejemplos_kanban_api.py)

---

## ✅ Checklist Final

- [ ] Archivos en su lugar
- [ ] URLs registradas
- [ ] Modelo verificado
- [ ] Base de datos migrada
- [ ] Servidor corriendo
- [ ] Kanban accesible en `/tareas/kanban/`
- [ ] Tareas visibles
- [ ] Drag-drop funciona
- [ ] Filtros funcionan
- [ ] Estadísticas actualizan

**¿Todos los puntos marcados? ¡Felicidades! Tu Kanban está listo para producción.** 🎉

---

**Documento:** Guía de Integración Rápida
**Versión:** 1.0
**Fecha:** Abril 2026
