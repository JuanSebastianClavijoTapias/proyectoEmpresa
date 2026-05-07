from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

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
    
    # Información del cliente
    nombre_cliente = models.CharField(max_length=200, verbose_name='Nombre del Cliente')
    telefono_cliente = models.CharField(max_length=255, verbose_name='Teléfono de Contacto')
    
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
    """Valida que el archivo sea una imagen y no exceda 10MB"""
    max_size = 10 * 1024 * 1024  # 10MB
    if fieldfile_obj.size > max_size:
        raise ValidationError('La imagen no puede superar los 10MB.')


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
        upload_to='tareas/imagenes/%Y/%m/',
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
        if self.imagen:
            self.imagen = self._comprimir_imagen(self.imagen)
        super().save(*args, **kwargs)

    def _comprimir_imagen(self, imagen):
        """Comprime y redimensiona la imagen para reducir almacenamiento"""
        img = Image.open(imagen)
        
        # Mantener orientación EXIF
        try:
            from PIL import ExifTags
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif is not None:
                orient = exif.get(orientation)
                if orient == 3:
                    img = img.rotate(180, expand=True)
                elif orient == 6:
                    img = img.rotate(270, expand=True)
                elif orient == 8:
                    img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass

        # Redimensionar si excede 1920px en cualquier lado
        max_dimension = 1920
        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        # Convertir a RGB si es necesario (para guardar como JPEG)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Comprimir como JPEG con calidad 75
        output = BytesIO()
        img.save(output, format='JPEG', quality=75, optimize=True)
        output.seek(0)

        # Generar nombre con extensión .jpg
        nombre = imagen.name.rsplit('.', 1)[0] + '.jpg'

        return InMemoryUploadedFile(
            output, 'ImageField', nombre, 'image/jpeg',
            sys.getsizeof(output), None
        )


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
