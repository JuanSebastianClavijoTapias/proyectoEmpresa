#!/bin/bash

# Script de Migración: Mover media a carpeta separada
# Ejecutar en la VPS en producción
# Uso: bash migrate-media.sh

set -e

echo "🔄 MIGRACIÓN DE MEDIA A CARPETA SEPARADA"
echo "========================================"
echo ""

# Variables
PROYECTO_DIR="/var/www/proyectoempresa"
MEDIA_VIEJO="$PROYECTO_DIR/proyectoempresa/media"
MEDIA_NUEVO="/var/www/media"  # FUERA del proyecto
BACKUP_DIR="/var/backups/migration-media-$(date +%Y%m%d-%H%M%S)"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Validaciones previas
echo "🔍 VALIDANDO ESTADO DEL SISTEMA..."
echo ""

if [ ! -d "$PROYECTO_DIR" ]; then
    log_error "Carpeta del proyecto no encontrada: $PROYECTO_DIR"
    exit 1
fi
log_info "Proyecto encontrado en $PROYECTO_DIR"

if [ ! -d "$MEDIA_VIEJO" ]; then
    log_warn "No hay carpeta media antigua en $MEDIA_VIEJO (puede estar OK si es nuevo deploy)"
else
    log_info "Carpeta media antigua encontrada: $MEDIA_VIEJO"
fi

# 2. Crear backup
echo ""
echo "💾 CREANDO BACKUP..."
mkdir -p "$BACKUP_DIR"
log_info "Backup dir: $BACKUP_DIR"

if [ -d "$MEDIA_VIEJO" ]; then
    cp -r "$MEDIA_VIEJO" "$BACKUP_DIR/media_old" || true
    log_info "Backup de media antigua completado"
fi

# Backup de settings.py por si acaso
cp "$PROYECTO_DIR/proyectoempresa/proyectoempresa/settings.py" "$BACKUP_DIR/settings.py.backup"
log_info "Backup de settings.py completado"

# 3. Crear estructura nueva
echo ""
echo "📁 CREANDO ESTRUCTURA DE CARPETAS..."

# Media (FUERA del proyecto)
sudo mkdir -p "$MEDIA_NUEVO"
log_info "Carpeta media creada: $MEDIA_NUEVO"

# Estáticos y logs (dentro del proyecto)
sudo mkdir -p "$PROYECTO_DIR/static"
sudo mkdir -p "$PROYECTO_DIR/logs"
log_info "Carpetas static y logs creadas"

# 4. Mover archivos viejos (si existen)
echo ""
echo "🚀 MIGRANDO ARCHIVOS DE MEDIA..."

if [ -d "$MEDIA_VIEJO" ] && [ "$(ls -A $MEDIA_VIEJO)" ]; then
    log_info "Moviendo archivos de $MEDIA_VIEJO → $MEDIA_NUEVO"
    sudo mv "$MEDIA_VIEJO"/* "$MEDIA_NUEVO/" || true
    log_info "Archivos movidos"
else
    log_info "No hay archivos antiguos para migrar (OK para nuevo deploy)"
fi

# 5. Establecer permisos
echo ""
echo "🔐 ESTABLECIENDO PERMISOS..."

# Media (FUERA del proyecto)
sudo chown -R www-data:www-data "$MEDIA_NUEVO"
sudo chmod -R 775 "$MEDIA_NUEVO"
log_info "Permisos configurados en media ($MEDIA_NUEVO)"

# Estáticos y logs (dentro del proyecto)
sudo chown -R www-data:www-data "$PROYECTO_DIR/static"
sudo chmod -R 755 "$PROYECTO_DIR/static"
log_info "Permisos configurados en static"

sudo chown -R www-data:www-data "$PROYECTO_DIR/logs"
sudo chmod -R 775 "$PROYECTO_DIR/logs"
log_info "Permisos configurados en logs"

# 6. Recolectar estáticos
echo ""
echo "📦 RECOLECTANDO ARCHIVOS ESTÁTICOS..."

cd "$PROYECTO_DIR"
source venv/bin/activate
python manage.py collectstatic --noinput --clear --no-input 2>&1 | tail -5
log_info "Archivos estáticos recolectados"

# 7. Verificar settings.py
echo ""
echo "🔍 VERIFICANDO SETTINGS.PY..."

if grep -q "MEDIA_ROOT = '/var/www/media'" "$PROYECTO_DIR/proyectoempresa/proyectoempresa/settings.py"; then
    log_info "settings.py ya tiene configuración correcta (MEDIA_ROOT = /var/www/media)"
else
    log_warn "settings.py podría no tener la configuración correcta de carpeta separada"
    log_warn "Verifica que contenga:"
    log_warn '  if not DEBUG:'
    log_warn '    MEDIA_ROOT = "/var/www/media"'
fi

# 8. Reiniciar servicios
echo ""
echo "♻️  REINICIANDO SERVICIOS..."

sudo systemctl restart proyectoempresa
log_info "Gunicorn reiniciado"

sudo systemctl restart nginx
log_info "Nginx reiniciado"

# 9. Verificaciones finales
echo ""
echo "✅ VERIFICACIONES FINALES..."
echo ""

# Verificar permisos
if [ -w "$MEDIA_NUEVO" ]; then
    log_info "Media folder es escribible"
else
    log_error "Media folder NO es escribible"
    exit 1
fi

# Verificar ocupación
MEDIA_SIZE=$(du -sh "$MEDIA_NUEVO" 2>/dev/null | cut -f1)
log_info "Tamaño de media: $MEDIA_SIZE"

# Verificar que django corre
if sudo systemctl is-active --quiet proyectoempresa; then
    log_info "Django (Gunicorn) está activo"
else
    log_error "Django (Gunicorn) NO está activo"
    exit 1
fi

# Verificar que nginx corre
if sudo systemctl is-active --quiet nginx; then
    log_info "Nginx está activo"
else
    log_error "Nginx NO está activo"
    exit 1
fi

# 10. Resumen
echo ""
echo "========================================"
echo -e "${GREEN}✓ MIGRACIÓN COMPLETADA EXITOSAMENTE${NC}"
echo "========================================"
echo ""
echo "📊 RESUMEN:"
echo "  • Media anterior: $MEDIA_VIEJO"
echo "  • Media nueva: $MEDIA_NUEVO (FUERA del proyecto)"
echo "  • Tamaño media: $MEDIA_SIZE"
echo "  • Backup en: $BACKUP_DIR"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "  1. Verificar logs: tail -f /var/www/proyectoempresa/logs/gunicorn_error.log"
echo "  2. Probar subida de imagen desde la app"
echo "  3. Verificar que imagenes se guardan en: /var/www/media/tareas/imagenes/"
echo ""
echo "🔍 VALIDAR EN NAVEGADOR:"
echo "  https://tu-dominio.com/media/tareas/imagenes/"
echo ""
echo "💾 SI ALGO SALE MAL, RESTAURAR CON:"
echo "  sudo systemctl stop proyectoempresa nginx"
echo "  sudo rm -rf /var/www/media/*"
echo "  sudo cp -r $BACKUP_DIR/media_old/* /var/www/media/"
echo "  sudo systemctl start proyectoempresa nginx"
echo ""
