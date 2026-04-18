# Sistema de Control de Acceso Basado en Roles (RBAC)

## Descripción General

Se ha implementado un sistema completo de control de acceso basado en tres roles (Administrador, Gerente, Trabajador) en la aplicación Django Cuir Tapicería.

**Fecha de implementación**: 2026-04-18

## Migraciones Aplicadas

Se han creado dos migraciones en `panelfinanzas/migrations/`:

1. **0006_alter_perfilusuario_rol.py** - Actualiza el campo `rol` en el modelo `PerfilUsuario` con las tres nuevas opciones:
   - `administrador` - Acceso total a todas las funcionalidades
   - `gerente` - Acceso a productos, finanzas básicas y productividad
   - `trabajador` - Acceso solo a tareas y productividad propia

2. **0007_migrate_roles_to_new_system.py** - Migración de datos que convierte automáticamente:
   - `jefe` → `administrador`
   - `trabajador` → `trabajador` (sin cambios)

**Aplicar migraciones:**
```bash
python manage.py migrate
```

## Matriz de Acceso por Rol

| Módulo | Administrador | Gerente | Trabajador |
|--------|--------------|---------|-----------|
| **TAREAS** |
| - Listar tareas | ✅ | ✅ | ✅ |
| - Crear tareas | ✅ | ✅ | ✅ |
| - Clientes | ✅ | ✅ | ✅ |
| **PRODUCTIVIDAD** |
| - Mi productividad | ✅ | ✅ | ✅ |
| - Listar trabajadores | ✅ | ✅ | ❌ |
| **FINANZAS** |
| - Productos (listar/crear/editar) | ✅ | ✅ | ❌ |
| - Historial de entregas | ✅ | ✅ | ❌ |
| - Reporte de ventas | ✅ | ❌ | ❌ |
| - Gastos (listar/crear/editar) | ✅ | ❌ | ❌ |
| **ANÁLISIS** |
| - Dashboard de KPIs | ✅ | ❌ | ❌ |
| - Análisis financiero | ✅ | ❌ | ❌ |
| - Objetivos | ✅ | ❌ | ❌ |
| - Rendimiento de trabajadores | ✅ | ✅ | ✅ |
| - Notas | ✅ | ✅ | ✅ |
| **ESTÁNDARES** |
| - Configuración completa | ✅ | ❌ | ❌ |

## Creación de Cuentas de Prueba

### Opción 1: Usando Django Shell (Interactivo)

```bash
python manage.py shell
```

Luego ejecutar:

```python
from django.contrib.auth.models import User
from panelfinanzas.models import PerfilUsuario

# CREAR ADMINISTRADOR
admin_user = User.objects.create_user(
    username='admin',
    email='admin@cuirtapiceria.com',
    password='admin123',
    first_name='Admin',
    last_name='System'
)
admin_user.perfil.rol = 'administrador'
admin_user.perfil.save()
print(f"✅ Administrador creado: {admin_user.username} (rol: {admin_user.perfil.get_rol_display()})")

# CREAR GERENTE
gerente_user = User.objects.create_user(
    username='gerente',
    email='gerente@cuirtapiceria.com',
    password='gerente123',
    first_name='Juan',
    last_name='Gerente'
)
gerente_user.perfil.rol = 'gerente'
gerente_user.perfil.save()
print(f"✅ Gerente creado: {gerente_user.username} (rol: {gerente_user.perfil.get_rol_display()})")

# CREAR TRABAJADOR
trabajador_user = User.objects.create_user(
    username='trabajador',
    email='trabajador@cuirtapiceria.com',
    password='trabajador123',
    first_name='Pedro',
    last_name='Trabajador'
)
trabajador_user.perfil.rol = 'trabajador'
trabajador_user.perfil.save()
print(f"✅ Trabajador creado: {trabajador_user.username} (rol: {trabajador_user.perfil.get_rol_display()})")

# Verificar que se crearon correctamente
print("\n📋 Usuarios creados:")
for user in User.objects.all():
    try:
        print(f"  - {user.username} ({user.perfil.get_rol_display()})")
    except:
        print(f"  - {user.username} (sin perfil)")
```

**Luego escribir `exit()` para salir del shell.**

### Opción 2: Usando un Script Python

Crear archivo `create_test_users.py` en la raíz del proyecto:

```python
#!/usr/bin/env python
import os
import django
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoempresa.settings')
django.setup()

from panelfinanzas.models import PerfilUsuario

test_users = [
    {
        'username': 'admin',
        'email': 'admin@cuirtapiceria.com',
        'password': 'admin123',
        'first_name': 'Admin',
        'last_name': 'System',
        'rol': 'administrador'
    },
    {
        'username': 'gerente',
        'email': 'gerente@cuirtapiceria.com',
        'password': 'gerente123',
        'first_name': 'Juan',
        'last_name': 'Gerente',
        'rol': 'gerente'
    },
    {
        'username': 'trabajador',
        'email': 'trabajador@cuirtapiceria.com',
        'password': 'trabajador123',
        'first_name': 'Pedro',
        'last_name': 'Trabajador',
        'rol': 'trabajador'
    }
]

print("🔄 Creando usuarios de prueba...\n")

for user_data in test_users:
    rol = user_data.pop('rol')
    username = user_data['username']
    
    # No crear si ya existe
    if User.objects.filter(username=username).exists():
        print(f"⚠️  Usuario '{username}' ya existe, omitiendo...")
        continue
    
    user = User.objects.create_user(**user_data)
    user.perfil.rol = rol
    user.perfil.save()
    print(f"✅ {rol.capitalize()} creado: {username}")

print("\n📋 Resumen de usuarios:")
for user in User.objects.all().order_by('username'):
    try:
        rol = user.perfil.get_rol_display()
        print(f"  • {user.username:15} → {rol:15} ({user.email})")
    except:
        print(f"  • {user.username:15} → Sin perfil")
```

Ejecutar:
```bash
python create_test_users.py
```

## Arquitectura de la Solución

### 1. Modelo de Base de Datos (`panelfinanzas/models.py`)

```python
class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('administrador', 'Administrador - Acceso total'),
        ('gerente', 'Gerente - Finanzas y productividad'),
        ('trabajador', 'Trabajador - Tareas y productividad'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='trabajador')
    
    # Propiedades de conveniencia
    @property
    def es_administrador(self):
        return self.rol == 'administrador'
    
    @property
    def es_gerente(self):
        return self.rol == 'gerente'
    
    @property
    def es_trabajador(self):
        return self.rol == 'trabajador'
    
    @property
    def es_jefe(self):  # Backward compatibility
        return self.rol in ['administrador', 'gerente']
```

### 2. Módulo de Permisos (`core/permissions.py`)

Contiene decoradores y mixins reutilizables:

- **Decoradores de función:**
  - `@require_role(*allowed_roles)` - Genérico, permite especificar múltiples roles
  - `@require_administrador` - Solo administrador
  - `@require_not_trabajador` - Administrador o Gerente
  - `@require_administrador_o_gerente` - Administrador o Gerente (alias)
  - `@require_gerente` - Solo Gerente

- **Mixins para vistas basadas en clases:**
  - `RoleRequiredMixin` - Base para cualquier rol requerido
  - `AdministradorRequiredMixin`
  - `NotTrabajadorMixin` (Administrador o Gerente)
  - Etc.

- **Funciones auxiliares:**
  - `user_has_role(user, *roles)` - Verificar si usuario tiene alguno de los roles
  - `user_can_access_finanzas(user)` - ¿Puede acceder a finanzas?
  - `user_can_access_gastos(user)` - ¿Puede acceder a gastos?
  - `user_can_access_analisis(user)` - ¿Puede acceder a análisis?
  - `user_can_access_estandares(user)` - ¿Puede acceder a estándares?

### 3. Aplicación de Decoradores

Todos los módulos aplican decoradores apropiados:

| Módulo | Decorador Usado | Restricción |
|--------|-----------------|-------------|
| panelfinanzas - productos | `@require_not_trabajador` | Bloquea trabajadores |
| panelfinanzas - reporte/gastos | `@require_administrador` | Solo admin |
| panelanalisis - dashboard/financiero/objetivos | `@require_administrador` | Solo admin |
| panelestandares - todas | `@require_administrador` | Solo admin |
| paneltareas - todas | `@login_required` | Todos autenticados |

### 4. Interfaz de Usuario (`templates/base.html`)

La navegación se filtra dinámicamente según el rol:

- **FINANZAS**: 
  - Admin ve "FINANZAS (ADMIN)" con todos los links
  - Gerente ve "FINANZAS (BÁSICO)" con solo productos/historial
  - Trabajador: no ve esta sección

- **ANÁLISIS**: 
  - Admin ve dashboard completo y análisis financiero
  - Otros: solo ven rendimiento de trabajadores y notas

- **ESTÁNDARES**: 
  - Solo admin ve esta sección

- **Insignia de usuario**: Color diferente según rol
  - Rojo (danger) = Administrador
  - Amarillo (warning) = Gerente
  - Gris (secondary) = Trabajador

### 5. Control de Acceso al Admin (`panelfinanzas/admin.py`)

El panel de admin de Django está restringido:
- Solo usuarios con rol `administrador` pueden acceder a `/admin/`
- Los superusuarios (`is_superuser=True`) siempre tienen acceso

## Verificación de la Implementación

### Test 1: Crear cuentas de prueba
```bash
python manage.py shell
# [Ejecutar script de creación de usuarios arriba]
```

### Test 2: Acceso a módulos como ADMINISTRADOR
1. Login con `admin` / `admin123`
2. Verificar que ve:
   - Dashboard de KPIs ✅
   - Análisis Financiero ✅
   - Todos los productos y gastos ✅
   - Estándares ✅
   - Panel de Admin ✅

### Test 3: Acceso a módulos como GERENTE
1. Login con `gerente` / `gerente123`
2. Verificar que ve:
   - Productos e Historial ✅
   - Reporte de ventas: ❌ (error 403)
   - Gastos: ❌ (error 403)
   - KPIs/Análisis: ❌ (error 403)
   - Estándares: ❌ (error 403)
   - Panel de Admin: ❌ (no aparece el link)

### Test 4: Acceso a módulos como TRABAJADOR
1. Login con `trabajador` / `trabajador123`
2. Verificar que ve:
   - Tareas y productividad ✅
   - Finanzas: ❌ (error 403)
   - KPIs/Análisis: ❌ (error 403)
   - Estándares: ❌ (error 403)

### Test 5: Intentar acceso directo a URLs restringidas

```bash
# Ejemplos de URLs que deberían retornar 403 para ciertos roles:

# Estas URLs requieren NO SER TRABAJADOR (admin/gerente):
/finanzas/productos/
/finanzas/productos/<id>/
/finanzas/historial/

# Estas URLs requieren SOLO ADMINISTRADOR:
/finanzas/reporte/
/finanzas/gastos/
/analisis/dashboard/
/analisis/financiero/
/estandares/

# Intento como trabajador: HTTP 403 Forbidden
curl -b "sessionid=<cookie>" http://localhost:8000/finanzas/reporte/
```

## Backward Compatibility (Compatibilidad Retroactiva)

Se mantiene la propiedad `es_jefe` en el modelo `PerfilUsuario`:

```python
@property
def es_jefe(self):
    return self.rol in ['administrador', 'gerente']
```

Esto permite que código antiguo que verificaba `user.perfil.es_jefe` siga funcionando, ya que ambos nuevos roles (administrador y gerente) tendrán acceso a funcionalidades tipo "jefe".

## Troubleshooting

### Problema: Usuario no ve su rol después del login

**Solución:** Verificar que el perfil se creó correctamente:
```python
python manage.py shell
>>> from django.contrib.auth.models import User
>>> u = User.objects.get(username='admin')
>>> u.perfil.rol
'administrador'
>>> u.perfil.get_rol_display()
'Administrador - Acceso total'
```

### Problema: Error "PerfilUsuario matching query does not exist"

**Causa:** Hay usuarios sin perfil asociado.
**Solución:** Reconstruir perfiles:
```python
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from panelfinanzas.models import PerfilUsuario
>>> for user in User.objects.all():
...     PerfilUsuario.objects.get_or_create(usuario=user)
```

### Problema: El admin no restringe acceso

**Verificar:**
1. Las migraciones se aplicaron correctamente: `python manage.py showmigrations panelfinanzas`
2. El archivo `core/permissions.py` existe y contiene `ROLE_ADMINISTRADOR`
3. Reiniciar el servidor Django: `python manage.py runserver`

## Archivos Modificados

### Archivos Creados
- `/core/__init__.py` - Nuevo módulo
- `/core/permissions.py` - Sistema RBAC (400+ líneas)
- `/panelfinanzas/migrations/0006_alter_perfilusuario_rol.py` - Migración de estructura
- `/panelfinanzas/migrations/0007_migrate_roles_to_new_system.py` - Migración de datos

### Archivos Modificados
- `/panelfinanzas/models.py` - Actualizado PerfilUsuario con 3 roles
- `/panelfinanzas/views.py` - 10 decoradores actualizados
- `/panelfinanzas/admin.py` - Restricción de acceso a admin
- `/panelanalisis/views.py` - 5 decoradores actualizados (dashboard, financiero, objetivos)
- `/panelestandares/views.py` - 8 decoradores actualizados (todas las vistas)
- `/paneltareas/views.py` - login_view mejorado con validación de rol
- `/templates/base.html` - Navegación filtrada por rol, colores de insignia

## Contacto y Soporte

Para preguntas sobre la implementación del sistema RBAC:
- Revisar este documento completo
- Consultar `/core/permissions.py` para ejemplos de uso de decoradores
- Ver cómo se usan los decoradores en `/panelfinanzas/views.py` como referencia

---

**Última actualización:** 2026-04-18 03:15 UTC
