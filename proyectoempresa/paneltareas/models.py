from django.db import models

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
