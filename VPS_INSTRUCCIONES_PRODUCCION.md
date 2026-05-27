# 🚀 Instrucciones para Poner en Producción en VPS

**Objetivo:** Desplegar ProyectoEmpresa en el servidor VPS con almacenamiento separado de media.

**Tiempo estimado:** 30-45 minutos

---

## ✅ Paso 1: Preparar la VPS

Conectarse por SSH al servidor:

```bash
ssh root@tu-vps.com
# Ingresar contraseña
```

---

## ✅ Paso 2: Crear Estructura de Carpetas

```bash
# Crear carpeta principal del proyecto
mkdir -p /var/www/proyectoempresa
cd /var/www/proyectoempresa

# Crear subcarpetas
mkdir -p {media,static,logs,venv}

# Crear usuario www-data si no existe (normalmente ya está)
# Establecer permisos correctos
sudo chown -R www-data:www-data /var/www/proyectoempresa
sudo chmod -R 775 /var/www/proyectoempresa

# Verificar
ls -la /var/www/proyectoempresa
# Debería mostrar: media, static, logs, venv
```

---

## ✅ Paso 3: Descargar Código

Opción A - Desde Git (si tienes repositorio):

```bash
cd /var/www/proyectoempresa
git clone https://tu-repositorio.git .
# (el punto final copia al directorio actual)
```

Opción B - Desde tu máquina local:

```bash
# En tu máquina local:
scp -r proyectoEmpresa/* root@tu-vps.com:/var/www/proyectoempresa/
```

---

## ✅ Paso 4: Instalar Dependencias del Sistema

En la VPS:

```bash
sudo apt update
sudo apt upgrade -y

# Instalar Python 3.12+ y herramientas
sudo apt install -y python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib \
    nginx \
    git \
    wget \
    curl

# Instalar Pillow (para procesamiento de imágenes)
sudo apt install -y python3-dev libjpeg-dev zlib1g-dev

# Verificar versiones
python3 --version  # Debe ser 3.12+
postgres --version
nginx -v
```

---

## ✅ Paso 5: Configurar Entorno Virtual

```bash
cd /var/www/proyectoempresa

# Crear entorno virtual
python3.12 -m venv venv

# Activar
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependencias del proyecto
pip install -r requirements.txt

# Verificar que Pillow se instaló correctamente
python -c "from PIL import Image; print('✓ Pillow OK')"
```

---

## ✅ Paso 6: Configurar Base de Datos PostgreSQL

En la VPS:

```bash
# Conectarse a PostgreSQL como admin
sudo -u postgres psql

# Crear usuario y base de datos
CREATE USER cuiruser WITH PASSWORD 'tu-contraseña-segura';
CREATE DATABASE cuirtapiceria OWNER cuiruser;

# Dar permisos
GRANT ALL PRIVILEGES ON DATABASE cuirtapiceria TO cuiruser;

# Salir
\q
```

**IMPORTANTE:** Cambiar la contraseña en `settings.py`:

```bash
nano /var/www/proyectoempresa/proyectoempresa/proyectoempresa/settings.py

# Buscar la sección DATABASES y verificar:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cuirtapiceria',
        'USER': 'cuiruser',
        'PASSWORD': 'tu-contraseña-segura',  # ← CAMBIAR AQUÍ
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Guardar: Ctrl+X, Y, Enter
```

---

## ✅ Paso 7: Crear Base de Datos (Migraciones)

```bash
cd /var/www/proyectoempresa
source venv/bin/activate

# Ejecutar migraciones (crear tablas)
python manage.py migrate

# Debería mostrar:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, ...
# Running migrations:
#   Applying admin.0001_initial... OK
#   ...
```

---

## ✅ Paso 8: Recolectar Archivos Estáticos

```bash
# En /var/www/proyectoempresa
python manage.py collectstatic --noinput

# Esto copia CSS, JavaScript a /var/www/proyectoempresa/static
# Debería mostrar: "X static files copied"
```

---

## ✅ Paso 9: Configurar Gunicorn (Servidor de Aplicación)

Crear archivo de servicio:

```bash
sudo nano /etc/systemd/system/proyectoempresa.service
```

Pegar lo siguiente:

```ini
[Unit]
Description=ProyectoEmpresa Django Application
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/proyectoempresa

# Activar entorno virtual y ejecutar gunicorn
ExecStart=/var/www/proyectoempresa/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --error-logfile /var/www/proyectoempresa/logs/gunicorn_error.log \
    --access-logfile /var/www/proyectoempresa/logs/gunicorn_access.log \
    --log-level info \
    proyectoempresa.wsgi:application

# Reiniciar automáticamente si falla
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Guardar: `Ctrl+X, Y, Enter`

Ahora activar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable proyectoempresa
sudo systemctl start proyectoempresa

# Verificar que está corriendo
sudo systemctl status proyectoempresa

# Ver logs
tail -20 /var/www/proyectoempresa/logs/gunicorn_error.log
```

---

## ✅ Paso 10: Configurar Nginx (Servidor Web)

Crear archivo de configuración:

```bash
sudo nano /etc/nginx/sites-available/proyectoempresa
```

Pegar lo siguiente (cambiar `tu-dominio.com`):

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Límite de tamaño de upload (8MB para fotos crudas)
    client_max_body_size 8M;

    # Redirigir HTTP a HTTPS (opcional, si tienes SSL)
    # return 301 https://$server_name$request_uri;

    # Servir estáticos directamente (CSS, JavaScript, etc)
    location /static/ {
        alias /var/www/proyectoempresa/static/;
        expires 30d;
        access_log off;
    }

    # Servir media (imágenes) directamente
    location /media/ {
        alias /var/www/proyectoempresa/media/;
        expires 7d;
        access_log off;
    }

    # Todo lo demás va a Django (Gunicorn)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Guardar: `Ctrl+X, Y, Enter`

Habilitar sitio:

```bash
sudo ln -s /etc/nginx/sites-available/proyectoempresa /etc/nginx/sites-enabled/

# Verificar sintaxis
sudo nginx -t
# Debería mostrar: "syntax is ok"

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## ✅ Paso 11: Configurar SSL (Let's Encrypt - OPCIONAL pero RECOMENDADO)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generar certificado (cambiar tu-dominio.com)
sudo certbot certonly --nginx -d tu-dominio.com -d www.tu-dominio.com

# Actualizar /etc/nginx/sites-available/proyectoempresa
sudo nano /etc/nginx/sites-available/proyectoempresa

# Cambiar la primera línea de:
#   listen 80;
# A:
#   listen 443 ssl http2;
#   ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
#   ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

# Y agregar redirección HTTP→HTTPS al final:
# server {
#     listen 80;
#     server_name tu-dominio.com www.tu-dominio.com;
#     return 301 https://$server_name$request_uri;
# }

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## ✅ Paso 12: Verificar que Todo Funciona

```bash
# Ver estado de servicios
sudo systemctl status proyectoempresa
sudo systemctl status nginx
sudo systemctl status postgresql

# Ver logs de errores
echo "=== GUNICORN ===" && tail -10 /var/www/proyectoempresa/logs/gunicorn_error.log
echo "=== NGINX ===" && sudo tail -10 /var/log/nginx/error.log

# Probar que responde
curl http://127.0.0.1:8000  # Debería retornar HTML
curl http://tu-dominio.com  # Debería retornar HTML

# Verificar que media se sirve
curl http://tu-dominio.com/media/  # Debería retornar 404 (porque no hay archivos)

# Probar subida de imagen
# Ir a: http://tu-dominio.com
# Crear una tarea con imagen
# Verificar que se guardó en: /var/www/proyectoempresa/media/tareas/imagenes/2026/05/
```

---

## ✅ Paso 13: Configurar Backups Automáticos (RECOMENDADO)

```bash
# Crear script de backup
sudo nano /usr/local/bin/backup-proyectoempresa.sh
```

Pegar:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/proyectoempresa"
mkdir -p $BACKUP_DIR

DATE=$(date +%Y%m%d_%H%M%S)

# Backup de base de datos
sudo -u postgres pg_dump cuirtapiceria | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup de media (imágenes)
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/proyectoempresa/media

# Guardar solo últimas 7 backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "✓ Backup realizado: $DATE"
```

Hacer ejecutable y programar:

```bash
sudo chmod +x /usr/local/bin/backup-proyectoempresa.sh

# Editar crontab para ejecutar diariamente a las 2 AM
sudo crontab -e

# Agregar línea:
# 0 2 * * * /usr/local/bin/backup-proyectoempresa.sh >> /var/log/backup.log 2>&1
```

---

## ✅ Paso 14: Monitorear Espacio en Disco

```bash
# Ver ocupación general
df -h

# Ver ocupación de media
du -sh /var/www/proyectoempresa/media

# Alertar si supera 80% de disco
df / | awk 'NR==2 {
    uso = $5;
    sub(/%/,"",uso);
    if (uso > 80) print "⚠️  ALERTA: Disco al " uso "%"
}'
```

---

## ✅ Paso 15: Si YA Tienes Imágenes (Migración)

Si ya hay un proycto en producción con imágenes en otra ubicación:

```bash
# Ejecutar script de migración (está en el repositorio)
cd /var/www/proyectoempresa
bash migrate-media.sh

# Esto automáticamente:
# - Hace backup de media vieja
# - Mueve archivos a la nueva ubicación
# - Establece permisos correctos
# - Reinicia servicios
```

---

## 🆘 Troubleshooting Rápido

| Problema                      | Solución                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------- |
| **Nginx retorna 502**         | Verificar que Gunicorn está corriendo: `sudo systemctl restart proyectoempresa` |
| **Permiso denegado en media** | Fijar permisos: `sudo chmod -R 775 /var/www/proyectoempresa/media`              |
| **Error de base de datos**    | Verificar conexión: `psql -U cuiruser -d cuirtapiceria -h localhost`            |
| **Imágenes no se ven**        | Verificar que existen: `ls -la /var/www/proyectoempresa/media/tareas/imagenes/` |
| **Alto uso de CPU**           | Revisar logs: `tail -50 /var/www/proyectoempresa/logs/gunicorn_error.log`       |

---

## 📊 Verificación Final

Después de completar todos los pasos, ejecutar:

```bash
# Usar el checklist completo
cd /var/www/proyectoempresa
bash VERIFICATION_CHECKLIST.md

# O verificar manualmente:
echo "✓ Carpetas:" && ls -d media static logs
echo "✓ Gunicorn:" && sudo systemctl is-active proyectoempresa
echo "✓ Nginx:" && sudo systemctl is-active nginx
echo "✓ PostgreSQL:" && sudo systemctl is-active postgresql
echo "✓ Media:" && curl -I http://localhost/media/ 2>/dev/null | head -1
```

---

## 📝 Notas Importantes

1. **Cambiar contraseña de BD** en `settings.py` por una segura
2. **DEBUG=False** debe estar activo en producción (ya está en settings.py)
3. **ALLOWED_HOSTS** debe incluir tu dominio en settings.py
4. **Backups son CRÍTICOS** - configurar automáticos
5. **Monitorear disco** - las imágenes crecen con el tiempo
6. **SSL es recomendado** - configura Let's Encrypt

---

## 📞 Si Algo Falla

1. Ver logs: `tail -50 /var/www/proyectoempresa/logs/gunicorn_error.log`
2. Revisar estado: `sudo systemctl status proyectoempresa`
3. Reintentar: `sudo systemctl restart proyectoempresa`
4. Si persiste, contactar al equipo de desarrollo con los logs

---

**Fecha:** 27 de mayo de 2026  
**Versión:** 1.0  
**Estado:** Listo para producción
