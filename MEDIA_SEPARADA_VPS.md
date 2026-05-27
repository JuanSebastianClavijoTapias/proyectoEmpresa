# 🚀 Implementar Media Separada en VPS

**Objetivo:** Guardar imágenes FUERA del proyecto para evitar lag

---

## 🔧 PASOS EN LA VPS

### Paso 1: SSH a la VPS

```bash
ssh ubuntu@tu-vps-ip
# O si tienes dominio
ssh ubuntu@tu-dominio.com
```

---

### Paso 2: Ir al proyecto

```bash
cd /home/ubuntu/apps/proyectoEmpresa/proyectoempresa
```

Estructura actual:

```
/home/ubuntu/apps/
├── proyectoEmpresa/        ← Código
│   ├── proyectoempresa/    ← App Django
│   ├── venv/               ← Entorno virtual
│   └── manage.py
└── media/                  ← 📁 CREAR AQUÍ (nueva carpeta)
```

---

### Paso 3: Crear carpeta de media FUERA del proyecto

```bash
# Posicionarse en /home/ubuntu/apps
cd /home/ubuntu/apps

# Crear carpeta media
mkdir -p media

# Dar permisos al usuario del servidor (ubuntu o www-data)
chmod 755 media
ls -la media
# Debería mostrar: drwxr-xr-x ubuntu ubuntu
```

---

### Paso 4: Traer cambios del código

```bash
# Entrar al proyecto
cd /home/ubuntu/apps/proyectoEmpresa/proyectoempresa

# Activar entorno virtual
source ../venv/bin/activate

# Traer cambios (settings.py actualizado)
git pull origin main

# Ver que los cambios están
cat proyectoempresa/settings.py | grep -A 5 "Media files"
# Debería mostrar:
#   MEDIA_ROOT = '/home/ubuntu/apps/media'
```

---

### Paso 5: Recolectar estáticos y migrar

```bash
# Recolectar estáticos
python manage.py collectstatic --noinput

# Migraciones
python manage.py migrate

# Debería mostrar: "No changes detected" (ok)
```

---

### Paso 6: Reiniciar Gunicorn

```bash
# Reiniciar el servicio
sudo systemctl restart proyectoempresa

# Verificar que está corriendo
sudo systemctl status proyectoempresa
# Debería mostrar: active (running)

# Ver logs
tail -20 /home/ubuntu/apps/proyectoEmpresa/proyectoempresa/logs/gunicorn_error.log
```

---

### Paso 7: Probar que funciona

#### Opción A: Desde la interfaz web

1. Ir a: `https://tu-dominio.com`
2. Crear una tarea
3. Subir una foto grande (>2MB)
4. Observar:
    - ✅ Response INMEDIATA (<1 segundo)
    - ✅ Tarea se crea al instante
    - ✅ Sin timeout
    - ✅ Sin LAG

#### Opción B: Verificar que se guardó en la carpeta correcta

```bash
# Ver si se creó la estructura
ls -la /home/ubuntu/apps/media/
# Debería mostrar: tareas/

# Ver imágenes guardadas
ls -la /home/ubuntu/apps/media/tareas/imagenes/2026/05/
# Debería mostrar: .jpg files

# Ver tamaño de las imágenes (deben ser <2MB)
du -h /home/ubuntu/apps/media/tareas/imagenes/2026/05/*
# Ejemplo: 380K, 420K, etc.
```

#### Opción C: Test de velocidad desde terminal

```bash
# Medir tiempo de respuesta
time curl https://tu-dominio.com/

# Debería ser: real 0m0.XXXs (muy rápido)
```

---

### Paso 8: Migrar imágenes viejas (si las hay)

Si ya tenías imágenes en `media/` dentro del proyecto, moverlas:

```bash
# Si existen imágenes viejas
if [ -d "/home/ubuntu/apps/proyectoEmpresa/proyectoempresa/media/tareas" ]; then
    echo "Moviendo imágenes viejas..."
    mv /home/ubuntu/apps/proyectoEmpresa/proyectoempresa/media/tareas/* \
       /home/ubuntu/apps/media/tareas/ 2>/dev/null || true

    # Eliminar la carpeta vieja
    rm -rf /home/ubuntu/apps/proyectoEmpresa/proyectoempresa/media

    echo "✓ Imágenes migradas"
else
    echo "No hay imágenes viejas"
fi
```

---

## ✅ Verificación Rápida

Ejecuta esto para confirmar que todo está bien:

```bash
echo "=== ESTRUCTURA ===" && \
ls -la /home/ubuntu/apps/ | grep -E 'media|proyectoEmpresa' && \
echo "" && \
echo "=== SETTINGS ===" && \
grep "MEDIA_ROOT" /home/ubuntu/apps/proyectoEmpresa/proyectoempresa/proyectoempresa/settings.py && \
echo "" && \
echo "=== GUNICORN ===" && \
sudo systemctl is-active proyectoempresa && \
echo "" && \
echo "=== PERMISOS ===" && \
ls -ld /home/ubuntu/apps/media
```

**Todo debería retornar OK.**

---

## 🎯 Resultado Final

```
/home/ubuntu/apps/
├── proyectoEmpresa/        ← 📁 CÓDIGO (limpio, sin imágenes)
│   └── proyectoempresa/
│       ├── media/          ← (carpeta vacía, solo por compatibilidad)
│       └── settings.py     ← (apunta a /home/ubuntu/apps/media)
└── media/                  ← 📁 IMÁGENES (aquí se guardan todas)
    └── tareas/imagenes/2026/05/
        ├── imagen1.jpg
        └── imagen2.jpg
```

**Beneficios:**

- ✅ Imágenes FUERA del código
- ✅ Si `/home/ubuntu/apps/media` crece, no afecta al servidor
- ✅ Sin LAG al subir fotos
- ✅ Fácil de escalar (montar disco adicional si es necesario)

---

## 🆘 Si Algo Falla

```bash
# Ver logs detallados
tail -50 /home/ubuntu/apps/proyectoEmpresa/proyectoempresa/logs/gunicorn_error.log

# Si dice "Permission denied"
chmod 777 /home/ubuntu/apps/media

# Si dice "media directory not found"
mkdir -p /home/ubuntu/apps/media
chmod 755 /home/ubuntu/apps/media

# Si sigue fallando, reiniciar
sudo systemctl restart proyectoempresa
```

---

**Versión:** 1.0  
**Fecha:** 27 de mayo de 2026  
**Estado:** Listo para producción
