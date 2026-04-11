# 🔐 CUENTAS DE TRABAJADOR - INSTRUCCIONES DE CONFIGURACIÓN

## 📋 Resumen
Se ha implementado un sistema completo de autenticación para trabajadores. Cada trabajador ahora tendrá:
- Una cuenta de usuario en la base de datos
- Acceso al portal con usuario y contraseña
- Dashboard personal de productividad
- Capacidad de registrar su productividad diaria

---

## 🚀 PASOS PARA IMPLEMENTAR

### PASO 1: Crear la Migración
Ejecuta este comando para agregar el campo `usuario` al modelo Trabajador:

```bash
python manage.py makemigrations panelproductividad
```

Esto creará un archivo de migración. Te pedirá que proporciones un valor por defecto:
- Escribe `1` para dejar el campo null (lo recomendado)

### PASO 2: Aplicar la Migración
Ejecuta:

```bash
python manage.py migrate panelproductividad
```

Este comando aplicará los cambios a tu base de datos.

### PASO 3: Crear el Grupo "trabajador" (OPCIONAL)
Si deseas que los usuarios tengan un rol específico:

```bash
python manage.py crear_usuarios_trabajadores --crear-grupo
```

### PASO 4: Crear Usuarios para Trabajadores Existentes
**Opción A: Generar contraseñas aleatorias (RECOMENDADO)**
```bash
python manage.py crear_usuarios_trabajadores
```

Esto:
- Busca todos los trabajadores sin usuario asignado
- Crea un usuario para cada uno
- Genera una contraseña aleatoria de 12 caracteres
- Asigna el grupo "trabajador" automáticamente
- Muestra un resumen con las credenciales

**Opción B: Usar una contraseña personalizada para todos**
```bash
python manage.py crear_usuarios_trabajadores --password "mi_contraseña_123"
```

---

## 📝 EJEMPLO DE SALIDA

```
📋 Creando usuarios para 3 trabajadores...

✓ Juan Pérez
✓ María García
✓ Carlos López

============================================================
✅ 3 usuarios creados exitosamente

📝 Resumen de Credenciales:

------------------------------------------------------------

👤 Trabajador: Juan Pérez
   Usuario: juan_perez
   Contraseña: K#x9@mL$2pQ!vR

👤 Trabajador: María García
   Usuario: maria_garcia
   Contraseña: nY7^bJ$4wZ#tP

👤 Trabajador: Carlos López
   Usuario: carlos_lopez
   Contraseña: sF2&dH!8jK%vL

============================================================

⚠️  IMPORTANTE: Guarden estas credenciales en un lugar seguro.
Los usuarios pueden cambiar su contraseña después de iniciar sesión.
```

---

## 🌐 ACCESO AL PORTAL

### Para Trabajadores:
1. Ir a: `http://localhost:8000/trabajador/login/`
2. Ingresar usuario y contraseña
3. Acceder al dashboard personal

### Rutas Disponibles:
- **Login**: `/trabajador/login/`
- **Dashboard**: `/trabajador/dashboard/` (requiere login)
- **Mi Productividad**: `/trabajador/productividad/` (requiere login)
- **Registrar Productividad**: `/trabajador/registrar/` (requiere login)
- **Logout**: `/trabajador/logout/`

---

## 🔧 CONFIGURACIÓN ADICIONAL (OPCIONAL)

### Para Cambiar Contrasena de un Trabajador:
```bash
python manage.py changepassword <username>
```

Ejemplo:
```bash
python manage.py changepassword juan_perez
```

### Para Ver Usuarios Creados:
```bash
python manage.py shell
```

Luego en el shell:
```python
from django.contrib.auth.models import User
usuarios = User.objects.filter(groups__name='trabajador')
for user in usuarios:
    print(f"{user.username}: {user.first_name} {user.last_name}")
```

### Para Eliminar un Usuario:
```python
from django.contrib.auth.models import User
user = User.objects.get(username='juan_perez')
user.delete()
```

---

## 🛡️ SEGURIDAD

✅ **Implementado:**
- Contraseñas hasheadas en la BD
- Autenticación por usuario/contraseña
- Session management automático
- CSRF protection en formularios

⚠️ **IMPORTANTE:**
- Nunca compartas contraseñas por email sin encriptar
- Cambia las credenciales después de proporcionarlas
- Usa HTTPS en producción
- Revisa regularmente los permisos de usuario

---

## ❓ PREGUNTAS FRECUENTES

**P: ¿Qué pasa si borro un trabajador?**
R: Su usuario de Django no se borra automáticamente. Debes borrarlo manualmente desde admin.

**P: ¿Puedo cambiar el nombre de usuario?**
R: No directamente. Debes crear uno nuevo y eliminar el anterior.

**P: ¿Qué información de productividad puede ver cada trabajador?**
R: Cada trabajador solo ve su propia información de productividad. Los administradores ven todo.

**P: ¿Cómo reinicio la contraseña de un trabajador?**
R: Usa `python manage.py changepassword <username>` desde la terminal.

---

## 📞 SOPORTE

Si necesitas ayuda con el sistema de autenticación:
1. Revisa los logs en: `Admin > Panelproductividad > Trabajadores`
2. Para errores, consulta la terminal donde corre Django
3. Los permisos se pueden configurar en Django Admin

---

**Última actualización:** 11/04/2026
**Estado:** ✅ Sistema completamente operativo
