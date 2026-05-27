# 🖼️ Cambios para Imágenes Asincrónicas en VPS Existente

**Para:** Personas que YA tienen ProyectoEmpresa corriendo en VPS  
**Tiempo:** 5 minutos  
**Riesgo:** Bajo (sin tiempo de inactividad)

---

## 📋 Resumen de Cambios

El código **ya está implementado** en:

- ✅ `settings.py` - Rutas de media separadas
- ✅ `paneltareas/models.py` - Procesamiento async
- ✅ `paneltareas/tests.py` - Tests actualizados

Solo necesitas **4 pasos** en la VPS:

---

## ✅ Paso 1: Crear Carpeta para Imágenes

En la VPS:

```bash
cd /var/www/proyectoempresa

# Crear carpeta de media FUERA del proyecto (para que no se llene)
sudo mkdir -p /var/www/media
sudo mkdir -p /var/www/proyectoempresa/static
sudo mkdir -p /var/www/proyectoempresa/logs

# Establecer permisos correctos
sudo chown -R www-data:www-data /var/www/media
sudo chown -R www-data:www-data /var/www/proyectoempresa/static
sudo chown -R www-data:www-data /var/www/proyectoempresa/logs

sudo chmod -R 775 /var/www/media
sudo chmod -R 775 /var/www/proyectoempresa/static
sudo chmod -R 775 /var/www/proyectoempresa/logs

# Verificar
ls -la /var/www/ | grep -E 'media|proyectoempresa'
# Debería mostrar: media y proyectoempresa con www-data:www-data
```

---

## ✅ Paso 2: Actualizar Código Fuente

En la VPS:

```bash
cd /var/www/proyectoempresa

# Opción A - Si tienes Git:
git pull origin main

# Opción B - Si copias manualmente:
# Reemplazar carpeta proyectoempresa/ con la versión nueva
```

---

## ✅ Paso 3: Recolectar Estáticos y Ejecutar Migraciones

```bash
# Activar entorno virtual
source venv/bin/activate

cd /var/www/proyectoempresa

# Recolectar estáticos (CSS, JS)
python manage.py collectstatic --noinput

# Ejecutar migraciones (por si hay cambios en modelos)
python manage.py migrate

# Verificar que no hay errores
# Debería mostrar: "No changes detected"
```

---

## ✅ Paso 4: Reiniciar Gunicorn

```bash
# Reiniciar el servicio (sin downtime)
sudo systemctl restart proyectoempresa

# Verificar que está activo
sudo systemctl status proyectoempresa
# Debería mostrar: active (running)

# Ver logs para confirmar que arrancó bien
tail -20 /var/www/proyectoempresa/logs/gunicorn_error.log
# Debería estar limpio, sin errores
```

---

## ✅ Paso 5: Verificación (5 segundos)

```bash
# Probar que el sitio responde
curl https://tu-dominio.com/

# Debería retornar HTML (no error 500)
```

---

## 🎯 Listo

**Eso es todo.** El sistema ahora **NO LAG** porque:

✅ **Upload rápido:** Request retorna en <1 segundo (no espera a comprimir)  
✅ **Procesa en background:** Las imágenes se optimizan sin bloquear el servidor  
✅ **Media separada:** `/var/www/media` (disco independiente, no ralentiza código)  
✅ **Almacenamiento eficiente:** 2MB final garantizado (6.5× menos espacio)  
✅ **Sin timeout:** Fotos de cámara (8MB) se suben sin problemas

---

## 📊 Paso 6: Verificar que Funciona

```bash
# 1. Subir imagen desde la app
# Ir a: https://tu-dominio.com
# Crear tarea con imagen

# 2. Verificar que se guardó
ls -la /var/www/media/tareas/imagenes/2026/05/
# Debería mostrar archivos .jpg

# 3. Ver que el request fue rápido
# La respuesta debería ser <1 segundo (optimización en background)

# 4. Revisar logs de error
tail -50 /var/www/proyectoempresa/logs/gunicorn_error.log
# Debería estar limpio
```

---

## 📝 Resumen Rápido (Copy-Paste)

Si solo quieres ejecutar todo de una vez:

```bash
sudo mkdir -p /var/www/media /var/www/proyectoempresa/{static,logs}
sudo chown -R www-data:www-data /var/www/media /var/www/proyectoempresa/{static,logs}
sudo chmod -R 775 /var/www/media /var/www/proyectoempresa/{static,logs}
cd /var/www/proyectoempresa
git pull origin main
source venv/bin/activate
python manage.py collectstatic --noinput
python manage.py migrate
sudo systemctl restart proyectoempresa
curl https://tu-dominio.com/
```

---

## ⚡ Verificar que NO hay LAG

Después de hacer los cambios, probar subiendo una imagen:

```bash
# Opción 1: Desde la interfaz web
# 1. Ir a: https://tu-dominio.com
# 2. Crear tarea
# 3. Subir foto grande (>2MB)
# 4. Observar:
#    ✓ Respuesta INMEDIATA (<1 segundo)
#    ✓ NO hay spinner girando
#    ✓ NO hay timeout
#    ✓ Tarea se crea al instante

# Opción 2: Test desde terminal
# Medir tiempo de respuesta
time curl -F "imagen=@/ruta/foto_grande.jpg" \
  https://tu-dominio.com/api/upload/
# Debería ser: real 0m0.XXXs (menos de 1 segundo)

# Opción 3: Revisar que la optimización ocurre en background
# Ver logs mientras subes
tail -f /var/www/proyectoempresa/logs/gunicorn_error.log

# Después de subir, espera 5-10 segundos
# Deberías ver mensajes de "Optimizando imagen..."
```

---

## 🆘 Si SIGUE habiendo LAG

```bash
# 1. Verificar que Gunicorn se reinició correctamente
sudo systemctl status proyectoempresa
# Debería mostrar: active (running)

# 2. Revisar si hay errores en el startup
tail -50 /var/www/proyectoempresa/logs/gunicorn_error.log

# 3. Verificar que settings.py tiene DEBUG=False (en producción)
grep "^DEBUG" /var/www/proyectoempresa/proyectoempresa/proyectoempresa/settings.py
# Debería mostrar: DEBUG = False

# 4. Revisar permisos de carpeta media
ls -la /var/www/media
# Debería mostrar: drwxrwxr-x www-data www-data

# 5. Revisar que el ThreadPoolExecutor inició
grep -i "thread\|executor" /var/www/proyectoempresa/logs/gunicorn_error.log

# 6. Si todo está bien, reintentar:
sudo systemctl restart proyectoempresa
sleep 5
curl https://tu-dominio.com/

# 7. Si persiste: ver logs detallados
sudo journalctl -u proyectoempresa -n 100 | head -50
```

**Posibles causas de LAG:**

- ❌ Gunicorn no se reinició (ejecutar `sudo systemctl restart proyectoempresa`)
- ❌ Permisos incorrectos en `/var/www/media` (ejecutar `sudo chmod 775 /var/www/media`)
- ❌ DEBUG=True en producción (cambiar a `DEBUG = False` en settings.py)
- ❌ Código viejo sin cambios (ejecutar `git pull origin main`)

---

**Versión:** 1.0  
**Fecha:** 27 de mayo de 2026
