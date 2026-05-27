import atexit
import logging
from concurrent.futures import ThreadPoolExecutor
from django.core.exceptions import ValidationError
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import close_old_connections, models, transaction
from PIL import Image, ImageOps, UnidentifiedImageError


logger = logging.getLogger(__name__)

MAX_FINAL_IMAGE_BYTES = 2 * 1024 * 1024
MAX_IMAGE_DIMENSION = 1920  # FIX: máx 1920 px preservando proporción
MIN_IMAGE_QUALITY = 65
MAX_IMAGE_QUALITY = 75  # FIX: calidad objetivo JPEG 75
MAX_RAW_UPLOAD_BYTES = getattr(settings, 'PANELTAREAS_MAX_IMAGE_UPLOAD_BYTES', 50 * 1024 * 1024)  # FIX: límite 50 MB (después de compresión cliente)
ASYNC_IMAGE_PROCESSING = getattr(settings, 'PANELTAREAS_PROCESAR_IMAGENES_ASYNC', True)
IMAGE_PROCESSOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix='paneltareas-imagenes')


atexit.register(IMAGE_PROCESSOR.shutdown, wait=False, cancel_futures=True)

class Cliente(models.Model):
    """Modelo para almacenar información de clientes"""
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Cliente')
    telefono = models.CharField(max_length=255, verbose_name='Teléfono')
    email = models.EmailField(blank=True, null=True, verbose_name='Correo Electrónico')
    direccion = models.CharField(max_length=300, blank=True, null=True, verbose_name='Dirección')
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.telefono}"


class TareaPlanificada(models.Model):
    """Modelo para planificar tareas/trabajos pendientes"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    CATEGORIA_CHOICES = [
        ('taller', 'Taller'),
        ('bus', 'Bus'),
    ]
    
    # Información del cliente
    nombre_cliente = models.CharField(max_length=200, verbose_name='Nombre del Cliente')
    telefono_cliente = models.CharField(max_length=255, blank=True, default='', verbose_name='Teléfono de Contacto')
    
    # Información del vehículo (simplificado)
    placa = models.CharField(max_length=255, blank=True, null=True, verbose_name='Placa del Vehículo')
    
    # Información del trabajo
    descripcion_trabajo = models.TextField(verbose_name='Qué se le debe hacer', blank=True, default='')
    
    # Fechas
    fecha_ingreso = models.DateField(verbose_name='Fecha de Ingreso')
    fecha_entrega = models.DateField(verbose_name='Fecha de Entrega Estimada')
    
    # Estado y prioridad
    estado = models.CharField(max_length=25, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    prioridad = models.CharField(max_length=25, choices=PRIORIDAD_CHOICES, default='media', verbose_name='Prioridad')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='taller', verbose_name='Categoría')
    
    # Observaciones
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    
    # Monto abonado por el cliente (solo visible para jefes/admin)
    monto_abonado = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0, 
        verbose_name='Monto Abonado',
        help_text='Monto que el cliente ha abonado del precio total'
    )
    
    # Metadatos
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    
    class Meta:
        verbose_name = 'Tarea Planificada'
        verbose_name_plural = 'Tareas Planificadas'
        ordering = ['fecha_entrega', '-prioridad']
    
    def __str__(self):
        placa_str = self.placa if self.placa else 'Sin placa'
        return f"{placa_str} - {self.nombre_cliente}"
    
    @property
    def dias_restantes(self):
        """Calcula los días restantes para la entrega"""
        from datetime import date
        if self.estado in ['completado', 'cancelado']:
            return 0
        delta = self.fecha_entrega - date.today()
        return delta.days
    
    @property
    def precio_total(self):
        """Calcula el precio total sumando todos los productos de la tarea"""
        total = Decimal('0')
        for pt in self.productos_tarea.all():
            total += pt.total_venta
        return total
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente (precio total - monto abonado)"""
        return self.precio_total - self.monto_abonado

    @property
    def dias_vencidos(self):
        """Retorna los días vencidos en valor absoluto (solo si está vencida)"""
        if self.dias_restantes < 0:
            return abs(self.dias_restantes)
        return 0


def validar_imagen(fieldfile_obj):
    """Valida el tamaño bruto de subida para proteger el request y el worker."""
    if fieldfile_obj.size > MAX_RAW_UPLOAD_BYTES:
        raise ValidationError('La imagen no puede superar los 8MB al subirse.')


def _nombre_optimizado(nombre_original):
    ruta = Path(nombre_original)
    carpeta = str(ruta.parent)
    nuevo_nombre = f'{ruta.stem or "imagen"}.jpg'
    if carpeta and carpeta != '.':
        return str(Path(carpeta) / nuevo_nombre)
    return nuevo_nombre


def _convertir_a_jpeg_base(imagen_entrada):
    # FIX: exif_transpose() puede devolver una imagen NUEVA distinta del argumento;
    # si es copia nueva y no es el valor retornado, esta función la cierra.
    imagen = ImageOps.exif_transpose(imagen_entrada)
    _cerrar_transpuesta = imagen is not imagen_entrada

    try:
        if imagen.mode in ('RGBA', 'LA') or (imagen.mode == 'P' and 'transparency' in imagen.info):
            # FIX: cerrar rgba en finally para liberar memoria siempre, incluso ante error
            rgba = imagen.convert('RGBA')
            try:
                fondo = Image.new('RGB', rgba.size, (255, 255, 255))
                fondo.paste(rgba, mask=rgba.getchannel('A'))
            finally:
                rgba.close()  # FIX: cierre garantizado de imagen intermedia RGBA
            return fondo  # caller es responsable de cerrar fondo

        if imagen.mode != 'RGB':
            resultado = imagen.convert('RGB')
            return resultado  # caller es responsable de cerrar resultado

        # imagen ya es RGB y es el valor retornado: el caller la cierra
        _cerrar_transpuesta = False
        return imagen

    finally:
        # FIX: cerrar la copia de exif_transpose si no es el valor retornado
        if _cerrar_transpuesta:
            try:
                imagen.close()
            except Exception:
                pass


def _optimizar_imagen_bytes(archivo_imagen, nombre_original):
    """Redimensiona y comprime la imagen sin bloquear el request principal."""
    try:
        with Image.open(archivo_imagen) as imagen_abierta:
            # FIX: _convertir_a_jpeg_base puede retornar una imagen NUEVA;
            # cerrarla en finally para liberar memoria siempre, incluso ante error
            imagen_base = _convertir_a_jpeg_base(imagen_abierta)
            try:
                resampling = getattr(Image, 'Resampling', Image).LANCZOS

                if imagen_base.width > MAX_IMAGE_DIMENSION or imagen_base.height > MAX_IMAGE_DIMENSION:
                    imagen_base.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), resampling)

                for calidad in range(MAX_IMAGE_QUALITY, MIN_IMAGE_QUALITY - 1, -5):
                    salida = BytesIO()
                    try:
                        imagen_base.save(salida, format='JPEG', quality=calidad, optimize=True, progressive=True)
                        if salida.tell() <= MAX_FINAL_IMAGE_BYTES:
                            salida.seek(0)
                            return salida.read(), _nombre_optimizado(nombre_original)
                    finally:
                        salida.close()  # FIX: liberar BytesIO siempre, incluso en return anticipado

                for dimension in (1120, 1024, 900, 768):
                    # FIX: cerrar cada copia redimensionada en su propio bloque finally
                    imagen_redimensionada = imagen_base.copy()
                    try:
                        imagen_redimensionada.thumbnail((dimension, dimension), resampling)
                        for calidad in range(MAX_IMAGE_QUALITY, MIN_IMAGE_QUALITY - 1, -5):
                            salida = BytesIO()
                            try:
                                imagen_redimensionada.save(salida, format='JPEG', quality=calidad, optimize=True, progressive=True)
                                if salida.tell() <= MAX_FINAL_IMAGE_BYTES:
                                    salida.seek(0)
                                    return salida.read(), _nombre_optimizado(nombre_original)
                            finally:
                                salida.close()  # FIX: liberar BytesIO siempre
                    finally:
                        imagen_redimensionada.close()  # FIX: liberar copia siempre

                # Último recurso: calidad mínima
                salida = BytesIO()
                try:
                    imagen_base.save(salida, format='JPEG', quality=MIN_IMAGE_QUALITY, optimize=True, progressive=True)
                    salida.seek(0)
                    return salida.read(), _nombre_optimizado(nombre_original)
                finally:
                    salida.close()  # FIX: liberar BytesIO siempre
            finally:
                # FIX: cerrar imagen_base si es distinta de imagen_abierta
                # (significa que _convertir_a_jpeg_base creó una copia nueva)
                if imagen_base is not imagen_abierta:
                    try:
                        imagen_base.close()
                    except Exception:
                        pass
    except UnidentifiedImageError as exc:
        raise ValidationError('El archivo subido no es una imagen válida.') from exc


def _procesar_imagen_tarea_en_segundo_plano(imagen_pk):
    close_old_connections()
    try:
        imagen_obj = ImagenTarea.objects.select_related('producto_tarea', 'tarea').get(pk=imagen_pk)
        if not imagen_obj.imagen:
            return

        nombre_anterior = imagen_obj.imagen.name
        with imagen_obj.imagen.open('rb') as archivo_imagen:
            contenido, nuevo_nombre = _optimizar_imagen_bytes(archivo_imagen, nombre_anterior)

        # FIX: usar solo el nombre base (sin directorio) para que FieldFile.save()
        # no duplique el prefijo de upload_to al preponer el directorio de nuevo.
        # P.ej. 'tareas/imagenes/2026/05/foto.jpg' → save('foto.jpg') → genera
        # correctamente 'tareas/imagenes/2026/05/foto.jpg' con upload_to aplicado.
        imagen_obj.imagen.save(Path(nuevo_nombre).name, ContentFile(contenido), save=False)
        ImagenTarea.objects.filter(pk=imagen_pk).update(imagen=imagen_obj.imagen.name)

        if nombre_anterior and nombre_anterior != imagen_obj.imagen.name and imagen_obj.imagen.storage.exists(nombre_anterior):
            imagen_obj.imagen.storage.delete(nombre_anterior)
    except Exception:
        logger.exception('No se pudo optimizar la imagen %s', imagen_pk)
    finally:
        close_old_connections()


def programar_optimizacion_imagen(imagen_pk):
    if ASYNC_IMAGE_PROCESSING:
        IMAGE_PROCESSOR.submit(_procesar_imagen_tarea_en_segundo_plano, imagen_pk)
        return

    _procesar_imagen_tarea_en_segundo_plano(imagen_pk)


class ImagenTarea(models.Model):
    """Modelo para almacenar imágenes del progreso de las tareas"""
    tarea = models.ForeignKey(TareaPlanificada, on_delete=models.CASCADE, related_name='imagenes', verbose_name='Tarea')
    producto_tarea = models.ForeignKey(
        'ProductoTarea',
        on_delete=models.CASCADE,
        related_name='imagenes',
        verbose_name='Producto de la tarea',
        null=True,
        blank=True,
    )
    imagen = models.ImageField(
        # En models.py, donde está el campo ImageField
        upload_to='tareas/%Y/%m/',
        verbose_name='Imagen',
        validators=[validar_imagen],
        max_length = 255,
    )
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')
    
    class Meta:
        verbose_name = 'Imagen de Tarea'
        verbose_name_plural = 'Imágenes de Tareas'
        ordering = ['-fecha_subida']

    def clean(self):
        super().clean()
        if self.producto_tarea_id:
            if self.tarea_id and self.tarea_id != self.producto_tarea.tarea_id:
                raise ValidationError({'producto_tarea': 'El producto seleccionado no pertenece a esta tarea.'})
            self.tarea = self.producto_tarea.tarea
    
    def __str__(self):
        if self.producto_tarea_id:
            return f"Imagen de {self.producto_tarea.nombre_producto} - {self.fecha_subida.strftime('%d/%m/%Y %H:%M')}"
        placa_str = self.tarea.placa if self.tarea.placa else 'Sin placa'
        return f"Imagen de {placa_str} - {self.fecha_subida.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        if self.producto_tarea_id:
            self.tarea = self.producto_tarea.tarea

        # FIX: CAUSA RAÍZ DEL CRASH EN SEGUNDA SUBIDA.
        # La comprobación anterior se hacía DESPUÉS de super().save(), momento en que
        # imagen_actual (DB) e self.imagen.name ya son idénticos → debe_optimizar
        # era siempre False → las imágenes crudas de móvil (8-15 MB) se guardaban
        # sin comprimir, agotando storage y causando errores en la segunda subida.
        # FIX: capturar el nombre anterior ANTES del save para comparación correcta.
        _es_nuevo = self._state.adding  # True solo en la primera inserción
        _nombre_imagen_antes = None
        if not _es_nuevo:
            # Solo consultar DB en actualizaciones; en inserciones siempre optimizar
            _nombre_imagen_antes = (
                type(self).objects
                .filter(pk=self.pk)
                .values_list('imagen', flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        debe_optimizar = bool(self.imagen) and not getattr(self, '_omitir_optimizacion_imagen', False)
        if debe_optimizar and not _es_nuevo:
            # Actualización: solo optimizar si la imagen realmente cambió
            debe_optimizar = _nombre_imagen_antes != self.imagen.name
        # Para registros nuevos (_es_nuevo=True): debe_optimizar queda True si hay imagen

        if debe_optimizar:
            transaction.on_commit(lambda pk=self.pk: programar_optimizacion_imagen(pk))


class ProductoTarea(models.Model):
    """Productos asociados a una tarea con precios al momento de la asignación"""
    
    tarea = models.ForeignKey(
        TareaPlanificada, 
        on_delete=models.CASCADE, 
        related_name='productos_tarea',
        verbose_name='Tarea'
    )
    producto = models.ForeignKey(
        'panelfinanzas.Producto', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='entregas',
        verbose_name='Producto'
    )
    nombre_producto = models.CharField(max_length=200, verbose_name='Nombre del Producto')
    placa = models.CharField(max_length=255, blank=True, default='', verbose_name='Placa del Vehículo')
    cantidad = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    precio_costo = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name='Precio de Costo'
    )
    precio_venta = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name='Precio de Venta'
    )
    ajuste_precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Ajuste de Precio',
        help_text='Valor positivo para cobrar más, negativo para descuento'
    )
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción del trabajo para este producto')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Producto de Tarea'
        verbose_name_plural = 'Productos de Tareas'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.nombre_producto} x{self.cantidad} - {self.tarea}"
    
    @property
    def ganancia_unitaria(self):
        """Ganancia por unidad"""
        return self.precio_venta - self.precio_costo
    
    @property
    def ganancia_total(self):
        """Ganancia total (considerando cantidad)"""
        return self.ganancia_unitaria * self.cantidad
    
    @property
    def total_venta(self):
        """Total de venta (incluye ajuste de precio)"""
        return (self.precio_venta * self.cantidad) + self.ajuste_precio
    
    @property
    def total_costo(self):
        """Total de costo"""
        return self.precio_costo * self.cantidad
    
    @property
    def porcentaje_ganancia(self):
        """Porcentaje de ganancia"""
        if self.precio_costo > 0:
            return ((self.precio_venta - self.precio_costo) / self.precio_costo) * 100
        return 0
