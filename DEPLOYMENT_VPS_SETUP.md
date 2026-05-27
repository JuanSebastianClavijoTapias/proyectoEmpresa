# Guía de Deployment en VPS - ProyectoEmpresa

**Fecha:** 27 de mayo de 2026

---

## 📋 Checklist Pre-Deployment

- [ ] VPS con Ubuntu 20.04 LTS o superior
- [ ] SSH configurado
- [ ] Python 3.8+
- [ ] PostgreSQL instalado
- [ ] Nginx instalado
- [ ] Certificado SSL (Let's Encrypt)

---

## 1. Preparación de la VPS

### 1.1 SSH a la VPS

```bash
ssh usuario@tu-vps.com
```

### 1.2 Crear estructura de carpetas

```bash
# Crear directorios principales
sudo mkdir -p /var/www/proyectoempresa
sudo mkdir -p /var/www/proyectoempresa/media
sudo mkdir -p /var/www/proyectoempresa/static
sudo mkdir -p /var/www/proyectoempresa/logs
sudo mkdir -p /var/www/proyectoempresa/venv

# Crear usuario específico para la app (recomendado)
# O usar www-data existente
sudo chown -R www-data:www-data /var/www/proyectoempresa
sudo chmod -R 755 /var/www/proyectoempresa
sudo chmod -R 775 /var/www/proyectoempresa/media
sudo chmod -R 775 /var/www/proyectoempresa/logs
```

### 1.3 Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y libpq-dev postgresql postgresql-contrib
sudo apt install -y nginx
sudo apt install -y git
```

---

## 2. Clonar y Configurar la Aplicación

### 2.1 Clonar repositorio

```bash
cd /var/www/proyectoempresa
# Si usas GitHub con SSH
git clone git@github.com:usuario/proyectoempresa.git .

# O HTTPS
git clone https://github.com/usuario/proyectoempresa.git .
```

### 2.2 Crear virtual environment

```bash
cd /var/www/proyectoempresa
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Instalar dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4 Crear `.env` o configurar variables

```bash
# Crear archivo de configuración (nunca en Git)
cat > .env << EOF
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
SECRET_KEY=tu-clave-super-secreta-aqui-cambiar
DATABASE_URL=postgresql://usuario:password@localhost:5432/cuirtapiceria
PANELTAREAS_PROCESAR_IMAGENES_ASYNC=True
EOF

chmod 600 .env
```

### 2.5 Actualizar `settings.py` para leer .env

```bash
# Instalar python-decouple (si no está en requirements.txt)
pip install python-decouple

# Luego en proyectoempresa/settings.py agregar:
```

```python
from decouple import config, Csv

DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())
SECRET_KEY = config('SECRET_KEY')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='cuirtapiceria'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

---

## 3. Configurar PostgreSQL

### 3.1 Crear base de datos

```bash
# Conectarse a PostgreSQL
sudo -u postgres psql

# Crear usuario
CREATE USER cuiruser WITH PASSWORD 'contraseña-segura-aqui';

# Crear base de datos
CREATE DATABASE cuirtapiceria OWNER cuiruser;

# Dar permisos
GRANT ALL PRIVILEGES ON DATABASE cuirtapiceria TO cuiruser;

# Salir
\q
```

### 3.2 Migrar base de datos

```bash
cd /var/www/proyectoempresa
source venv/bin/activate

python manage.py migrate
python manage.py createsuperuser  # Crear admin

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

---

## 4. Configurar Nginx

### 4.1 Crear configuración de sitio

```bash
sudo nano /etc/nginx/sites-available/proyectoempresa
```

Contenido:

```nginx
upstream proyectoempresa {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # Certificados SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logs
    access_log /var/www/proyectoempresa/logs/nginx_access.log;
    error_log /var/www/proyectoempresa/logs/nginx_error.log;

    # Body size para uploads
    client_max_body_size 10M;

    # Archivos estáticos (CSS, JS, Admin)
    location /static/ {
        alias /var/www/proyectoempresa/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Imágenes de usuarios (Media) - SEPARADO
    location /media/ {
        alias /var/www/proyectoempresa/media/;
        expires 7d;
        access_log off;
    }

    # Django app
    location / {
        proxy_pass http://proyectoempresa;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### 4.2 Habilitar sitio

```bash
sudo ln -s /etc/nginx/sites-available/proyectoempresa \
           /etc/nginx/sites-enabled/proyectoempresa

# Verificar sintaxis
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx
```

### 4.3 Configurar SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y

sudo certbot certonly --nginx -d tu-dominio.com -d www.tu-dominio.com

# Auto-renovación
sudo systemctl enable certbot.timer
```

---

## 5. Configurar Gunicorn (App Server)

### 5.1 Crear servicio systemd

```bash
sudo nano /etc/systemd/system/proyectoempresa.service
```

Contenido:

```ini
[Unit]
Description=ProyectoEmpresa Gunicorn Server
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/proyectoempresa
Environment="PATH=/var/www/proyectoempresa/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=proyectoempresa.settings"
EnvironmentFile=/var/www/proyectoempresa/.env

ExecStart=/var/www/proyectoempresa/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --worker-tmp-dir /dev/shm \
    --bind 127.0.0.1:8000 \
    --timeout 300 \
    --access-logfile /var/www/proyectoempresa/logs/gunicorn_access.log \
    --error-logfile /var/www/proyectoempresa/logs/gunicorn_error.log \
    proyectoempresa.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 Habilitar servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable proyectoempresa
sudo systemctl start proyectoempresa
sudo systemctl status proyectoempresa
```

### 5.3 Instalar Gunicorn

```bash
source /var/www/proyectoempresa/venv/bin/activate
pip install gunicorn
```

---

## 6. Validar Permisos de Media

```bash
# Asegurar que la carpeta de media es escribible por www-data
sudo chown -R www-data:www-data /var/www/proyectoempresa/media
sudo chmod -R 775 /var/www/proyectoempresa/media

# Verificar
ls -la /var/www/proyectoempresa/media
```

---

## 7. Monitoreo y Logs

### 7.1 Ver logs

```bash
# Gunicorn
tail -f /var/www/proyectoempresa/logs/gunicorn_error.log

# Nginx
tail -f /var/www/proyectoempresa/logs/nginx_error.log

# Django
tail -f /var/www/proyectoempresa/logs/django.log  # Si lo configuras
```

### 7.2 Monitor de ocupación de media

```bash
# Crear script de monitoreo
cat > /usr/local/bin/check-media-size.sh << 'EOF'
#!/bin/bash
MEDIA_DIR="/var/www/proyectoempresa/media"
USAGE=$(du -sh "$MEDIA_DIR" | cut -f1)
PERCENT=$(df "$MEDIA_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')

echo "Media Storage: $USAGE (Disco: ${PERCENT}%)"

if [ "$PERCENT" -gt 80 ]; then
    echo "⚠️  ALERTA: Media storage al ${PERCENT}%"
    # Enviar email si necesario
    # echo "Alert" | mail -s "VPS Alert" admin@mail.com
fi
EOF

chmod +x /usr/local/bin/check-media-size.sh

# Agregar a cron (cada hora)
(sudo crontab -l 2>/dev/null; echo "0 * * * * /usr/local/bin/check-media-size.sh") | sudo crontab -
```

---

## 8. Backup

### 8.1 Backup de base de datos

```bash
# Script de backup
cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/proyectoempresa"
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
sudo -u postgres pg_dump cuirtapiceria | gzip > "$BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz"

# Mantener solo últimos 7 días
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-db.sh

# Ejecutar diariamente a las 2 AM
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-db.sh") | sudo crontab -
```

### 8.2 Backup de media (imágenes)

```bash
# Script de backup de media
cat > /usr/local/bin/backup-media.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/proyectoempresa-media"
mkdir -p "$BACKUP_DIR"

# Tar + gzip media folder
tar --exclude='*.tmp' -czf "$BACKUP_DIR/media_$(date +%Y%m%d_%H%M%S).tar.gz" \
    /var/www/proyectoempresa/media/

# Mantener solo últimos 30 días
find "$BACKUP_DIR" -name "media_*.tar.gz" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-media.sh

# Ejecutar semanalmente (domingos a las 3 AM)
(sudo crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/local/bin/backup-media.sh") | sudo crontab -
```

---

## 9. Troubleshooting

### Problema: "Permission denied" en media

```bash
sudo chown -R www-data:www-data /var/www/proyectoempresa/media
sudo chmod -R 775 /var/www/proyectoempresa/media
```

### Problema: "413 Payload Too Large"

Ya está configurado en Nginx (`client_max_body_size 10M`), pero si necesitas cambiar:

```nginx
# En /etc/nginx/sites-available/proyectoempresa
client_max_body_size 20M;  # Aumentar si necesario
```

### Problema: Las imágenes no cargan

```bash
# Verificar que Nginx puede acceder a media
ls -la /var/www/proyectoempresa/media/
# Debe ser accesible por www-data

# Verificar configuración de Nginx
sudo nginx -t
```

### Problema: Base de datos no conecta

```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Verificar contraseña en .env
grep DB_PASSWORD /var/www/proyectoempresa/.env

# Test de conexión
psql -h localhost -U cuiruser -d cuirtapiceria
```

---

## 10. Post-Deployment

### Verificar deployment

```bash
# Ver que todo está activo
sudo systemctl status proyectoempresa
sudo systemctl status nginx
sudo systemctl status postgresql

# Probar acceso web
curl https://tu-dominio.com

# Verificar que media se sirve
curl https://tu-dominio.com/media/tareas/imagenes/
```

### Test de subida de imagen

```bash
# Desde navegador o curl
curl -F "imagen=@/ruta/foto.jpg" https://tu-dominio.com/api/upload/

# Verificar que se guardó
ls -la /var/www/proyectoempresa/media/tareas/imagenes/
```

---

## 11. Mantenimiento Regular

### Semanal

```bash
# Revisar logs
tail -100 /var/www/proyectoempresa/logs/gunicorn_error.log
tail -100 /var/www/proyectoempresa/logs/nginx_error.log

# Verificar espacio
df -h
/usr/local/bin/check-media-size.sh
```

### Mensual

```bash
# Actualizar dependencias (con cuidado)
source /var/www/proyectoempresa/venv/bin/activate
pip list --outdated

# Ejecutar tests
python manage.py test

# Verificar integridad de BD
python manage.py dbshell < /dev/null
```

### Trimestral

```bash
# Revisar backups
ls -la /var/backups/proyectoempresa/
ls -la /var/backups/proyectoempresa-media/

# Probar restore (en staging)
# gunzip < db_backup.sql.gz | psql -U cuiruser -d cuirtapiceria_test
```

---

## 12. Checklist Final

- [ ] VPS configurada
- [ ] Django corriendo (Gunicorn activo)
- [ ] Nginx sirviendo
- [ ] Base de datos funcional
- [ ] SSL funcionando
- [ ] Media folder en `/var/www/proyectoempresa/media`
- [ ] Permisos de media correctos (775)
- [ ] Subida de imágenes probada
- [ ] Logs monitoreados
- [ ] Backups configurados
- [ ] Monitor de espacio activo

---

## 📞 Soporte

Si algo falla:

1. **Revisar logs**: `tail -f /var/www/proyectoempresa/logs/gunicorn_error.log`
2. **Reiniciar servicios**: `sudo systemctl restart proyectoempresa nginx`
3. **Verificar permisos**: `ls -la /var/www/proyectoempresa/media/`
4. **Conectarse a BD**: `psql -U cuiruser -d cuirtapiceria`

---

**Actualizado:** 27 de mayo de 2026  
**Versión:** 1.0
