from django.db import models
from decimal import Decimal

class Cliente(models.Model):
    """Modelo para almacenar información de clientes"""
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Cliente')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
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
    telefono_cliente = models.CharField(max_length=20, verbose_name='Teléfono de Contacto')
    
    # Información del vehículo (simplificado)
    placa = models.CharField(max_length=20, verbose_name='Placa del Vehículo')
    
    # Información del trabajo
    descripcion_trabajo = models.TextField(verbose_name='Qué se le debe hacer')
    
    # Fechas
    fecha_ingreso = models.DateField(verbose_name='Fecha de Ingreso')
    fecha_entrega = models.DateField(verbose_name='Fecha de Entrega Estimada')
    
    # Estado y prioridad
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='media', verbose_name='Prioridad')
    
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
        return f"{self.placa} - {self.nombre_cliente}"
    
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


class ImagenTarea(models.Model):
    """Modelo para almacenar imágenes del progreso de las tareas"""
    tarea = models.ForeignKey(TareaPlanificada, on_delete=models.CASCADE, related_name='imagenes', verbose_name='Tarea')
    imagen = models.ImageField(upload_to='tareas/imagenes/%Y/%m/', verbose_name='Imagen')
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')
    
    class Meta:
        verbose_name = 'Imagen de Tarea'
        verbose_name_plural = 'Imágenes de Tareas'
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f"Imagen de {self.tarea.placa} - {self.fecha_subida.strftime('%d/%m/%Y %H:%M')}"


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
        """Total de venta"""
        return self.precio_venta * self.cantidad
    
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
