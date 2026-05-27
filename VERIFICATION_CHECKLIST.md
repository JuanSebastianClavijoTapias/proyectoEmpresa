# Checklist de Verificación Post-Deploy

**Proyecto:** ProyectoEmpresa  
**Fecha:** 27 de mayo de 2026  
**Objetivo:** Validar que la separación de media está correcta en producción

---

## ✅ Paso 1: Verificar Estructura de Carpetas

### En la VPS, ejecuta:

```bash
# Ir a la carpeta del proyecto
cd /var/www/proyectoempresa

# Verificar que existen las carpetas separadas
ls -la | grep media
ls -la | grep static
ls -la | grep logs

# Debería mostrar:
# drwxr-xr-x ... media
# drwxr-xr-x ... static
# drwxr-xr-x ... logs
```

**Esperado:** ✅

- [ ] Carpeta `media` existe
- [ ] Carpeta `static` existe
- [ ] Carpeta `logs` existe

**Si falla:**

```bash
sudo mkdir -p /var/www/proyectoempresa/{media,static,logs}
sudo chown -R www-data:www-data /var/www/proyectoempresa/{media,static,logs}
sudo chmod -R 775 /var/www/proyectoempresa/{media,static,logs}
```

---

## ✅ Paso 2: Verificar Permisos

```bash
# Verificar que www-data puede escribir en media
ls -la /var/www/proyectoempresa/media
# Debe mostrar: drwxrwxr-x www-data www-data

# Test de escritura
touch /tmp/test.txt
sudo mv /tmp/test.txt /var/www/proyectoempresa/media/test.txt
if [ -f /var/www/proyectoempresa/media/test.txt ]; then
    echo "✓ www-data puede escribir en media"
    rm /var/www/proyectoempresa/media/test.txt
else
    echo "✗ www-data NO puede escribir en media"
fi
```

**Esperado:** ✅

- [ ] www-data puede escribir en `/var/www/proyectoempresa/media`
- [ ] Permisos son 775

**Si falla:**

```bash
sudo chown -R www-data:www-data /var/www/proyectoempresa/media
sudo chmod -R 775 /var/www/proyectoempresa/media
```

---

## ✅ Paso 3: Verificar settings.py

```bash
# Verificar que settings.py tiene la configuración correcta
grep -A 5 "if not DEBUG:" /var/www/proyectoempresa/proyectoempresa/proyectoempresa/settings.py

# Debe mostrar algo como:
# if not DEBUG:
#     MEDIA_ROOT = '/var/www/proyectoempresa/media'
#     STATIC_ROOT = '/var/www/proyectoempresa/static'
```

**Esperado:** ✅

- [ ] `MEDIA_ROOT` apunta a `/var/www/proyectoempresa/media`
- [ ] `STATIC_ROOT` apunta a `/var/www/proyectoempresa/static`
- [ ] `DEBUG=False` en producción

**Si no está configurado:**

```bash
# Ver archivo
cat /var/www/proyectoempresa/proyectoempresa/proyectoempresa/settings.py | grep -A 10 "MEDIA"

# Si no tiene la configuración, editarlo manualmente
# O restaurar desde deployment_guide
```

---

## ✅ Paso 4: Verificar que Gunicorn Está Corriendo

```bash
# Ver estado
sudo systemctl status proyectoempresa

# Debería mostrar: active (running)

# Ver logs
sudo tail -20 /var/www/proyectoempresa/logs/gunicorn_error.log

# Buscar errores
sudo grep ERROR /var/www/proyectoempresa/logs/gunicorn_error.log | tail -10
```

**Esperado:** ✅

- [ ] `proyectoempresa` está `active (running)`
- [ ] No hay errores en logs
- [ ] Últimas líneas muestran que app está respondiendo

**Si falla:**

```bash
sudo systemctl restart proyectoempresa
sudo systemctl status proyectoempresa

# Ver detalle del error
sudo journalctl -u proyectoempresa -n 50
```

---

## ✅ Paso 5: Verificar que Nginx Está Sirviendo Media

```bash
# Verificar configuración Nginx
sudo grep -A 5 "location /media/" /etc/nginx/sites-enabled/proyectoempresa

# Debería mostrar:
# location /media/ {
#     alias /var/www/proyectoempresa/media/;

# Verificar que nginx está activo
sudo systemctl status nginx

# Probar que sirve media
curl -I https://tu-dominio.com/media/

# Si está securizado con SSL:
# Debería retornar: HTTP/2 200 o 404 (no 500)
```

**Esperado:** ✅

- [ ] Nginx configuración tiene `location /media/`
- [ ] Nginx está `active (running)`
- [ ] `curl` retorna 200 o 404 (no 500)

**Si falla:**

```bash
sudo nginx -t  # Verifica sintaxis
sudo systemctl reload nginx
```

---

## ✅ Paso 6: Test de Subida de Imagen

### Desde la interfaz web:

1. **Abrir aplicación:** https://tu-dominio.com
2. **Ir a:** Crear tarea
3. **Agregar producto**
4. **Subir una imagen de prueba** (pequeña, <2MB)
5. **Verificar que:**
    - ✅ La imagen se subió exitosamente
    - ✅ Se muestra en el detalle de la tarea
    - ✅ No hay errores en logs

### Desde terminal (verificar archivo):

```bash
# Ver si se guardó la imagen
ls -la /var/www/proyectoempresa/media/tareas/imagenes/2026/05/

# Debería mostrar archivos .jpg

# Verificar que no están en la carpeta vieja
ls -la /var/www/proyectoempresa/proyectoempresa/media/ 2>/dev/null || echo "Carpeta no existe (correcto)"
```

**Esperado:** ✅

- [ ] Imagen se subió sin errores
- [ ] Archivo existe en `/var/www/proyectoempresa/media/tareas/imagenes/2026/05/`
- [ ] Es un .jpg comprimido
- [ ] Tamaño < 2MB

**Si falla:**

```bash
# Ver error en logs
tail -50 /var/www/proyectoempresa/logs/gunicorn_error.log

# Verificar permisos de nuevo
ls -la /var/www/proyectoempresa/media/
```

---

## ✅ Paso 7: Verificar Optimización Asíncrona

```bash
# Subir imagen grande (simulando foto de cámara)
# La optimización debería ocurrir en background

# Ver que request retorna rápido (<1 segundo)
time curl -F "imagen=@/ruta/foto_grande.jpg" https://tu-dominio.com/api/upload/

# Esperar ~10 segundos
sleep 10

# Verificar que archivo se optimizó (tamaño debe haber bajado)
ls -la /var/www/proyectoempresa/media/tareas/imagenes/2026/05/ | sort -k5 -n
```

**Esperado:** ✅

- [ ] Request retorna en <1 segundo (no se bloquea)
- [ ] Archivo final es .jpg
- [ ] Tamaño < 2MB
- [ ] No hay errores en logs durante optimización

**Si hay problemas:**

```bash
# Verificar ThreadPoolExecutor está activo
grep "ASYNC" /var/www/proyectoempresa/.env
# Debe mostrar: PANELTAREAS_PROCESAR_IMAGENES_ASYNC=True

# Ver si hay errores en log de optimización
grep -i "optimize" /var/www/proyectoempresa/logs/gunicorn_error.log
```

---

## ✅ Paso 8: Monitorear Espacio en Disco

```bash
# Ver ocupación general
df -h

# Ver ocupación específica de media
du -sh /var/www/proyectoempresa/media

# Ver ocupación del proyecto completo
du -sh /var/www/proyectoempresa

# Alertas si:
# - Media > 100GB
# - Disco total > 80% lleno
```

**Esperado:** ✅

- [ ] Disco principal < 80% lleno
- [ ] Media folder accesible
- [ ] Tamaño de media es razonable

**Si está cerca del límite:**

```bash
# Ver archivos más grandes
find /var/www/proyectoempresa/media -type f -exec ls -lh {} \; | sort -k5 -h | tail -20

# Ver carpetas más grandes
du -sh /var/www/proyectoempresa/media/*
```

---

## ✅ Paso 9: Verificar Logs

```bash
# Revisar últimas líneas de error
echo "=== GUNICORN ERRORS ==="
tail -20 /var/www/proyectoempresa/logs/gunicorn_error.log

echo ""
echo "=== NGINX ERRORS ==="
tail -20 /var/www/proyectoempresa/logs/nginx_error.log

echo ""
echo "=== SYSTEMD LOGS ==="
sudo journalctl -u proyectoempresa -n 10
```

**Esperado:** ✅

- [ ] No hay errores `ERROR` o `CRITICAL`
- [ ] Warnings son normales
- [ ] Logs muestran que app está respondiendo

---

## ✅ Paso 10: Backup y Recuperación

```bash
# Verificar que backups existen
ls -la /var/backups/proyectoempresa*/

# Debería mostrar:
# - db_*.sql.gz (backups de BD)
# - media_*.tar.gz (backups de imágenes)

# Test de restauración (SOLO EN STAGING, NO EN PRODUCCIÓN):
# gunzip < /var/backups/proyectoempresa/db_YYYYMMDD.sql.gz | psql -U cuiruser -d test_cuirtapiceria
```

**Esperado:** ✅

- [ ] Existen backups de BD
- [ ] Existen backups de media (si se configuró)
- [ ] Backups tienen timestamps recientes

---

## 📊 Resumen de Verificación

Marca lo que pasó:

### Infraestructura

- [ ] Carpetas en lugar correcto (`/var/www/proyectoempresa/media`)
- [ ] Permisos correctos (775, www-data)
- [ ] settings.py configurado para separar media
- [ ] Gunicorn activo
- [ ] Nginx activo

### Funcionalidad

- [ ] Subida de imagen funciona
- [ ] Imagen se guarda en media folder correcto
- [ ] Optimización asíncrona ocurre
- [ ] Archivo final es < 2MB
- [ ] No hay errores en logs

### Monitoreo

- [ ] Espacio en disco monitoreado
- [ ] Backups configurados
- [ ] Logs siendo guardados
- [ ] AlertaseActivas (si se configuró)

---

## 🆘 Si algo falla

### Checklist de troubleshooting rápido

```bash
# 1. Ver estado general
sudo systemctl status proyectoempresa nginx postgresql

# 2. Revisar logs
tail -50 /var/www/proyectoempresa/logs/gunicorn_error.log
sudo tail -50 /var/log/nginx/error.log

# 3. Verificar conexión BD
psql -U cuiruser -d cuirtapiceria -c "SELECT 1;"

# 4. Reiniciar servicios
sudo systemctl restart proyectoempresa
sudo systemctl restart nginx

# 5. Ver si problema persiste
# Probar subida de imagen de nuevo
```

### Contacto para soporte

Si el problema persiste:

1. Tomar screenshot del error
2. Ejecutar: `sudo journalctl -u proyectoempresa -n 200 > /tmp/debug.log`
3. Compartir `/tmp/debug.log` con el equipo de desarrollo

---

**Checklist versión:** 1.0  
**Última actualización:** 27 de mayo de 2026
