from django.db import models
from django.contrib.auth.models import User


class ObjetivoMensual(models.Model):
    """Objetivos/metas mensuales para medir rendimiento"""
    
    mes = models.DateField(
        verbose_name='Mes',
        help_text='Seleccione el primer día del mes'
    )
    
    # Objetivos financieros
    meta_ingresos = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Meta de Ingresos',
        help_text='Ingreso total esperado en el mes'
    )
    meta_ganancia = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Meta de Ganancia',
        help_text='Ganancia neta esperada en el mes'
    )
    
    # Objetivos operativos
    meta_tareas_completadas = models.PositiveIntegerField(
        default=0,
        verbose_name='Meta de Tareas Completadas',
        help_text='Cantidad de tareas a completar en el mes'
    )
    meta_clientes_nuevos = models.PositiveIntegerField(
        default=0,
        verbose_name='Meta de Clientes Nuevos',
        help_text='Cantidad de clientes nuevos esperados'
    )
    
    # Objetivos de productividad
    meta_items_producidos = models.PositiveIntegerField(
        default=0,
        verbose_name='Meta de Items Producidos',
        help_text='Total de items/piezas a producir en el mes'
    )
    
    # Metadatos
    notas = models.TextField(blank=True, verbose_name='Notas y Observaciones')
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Creado por'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Objetivo Mensual'
        verbose_name_plural = 'Objetivos Mensuales'
        ordering = ['-mes']
        unique_together = ['mes']
    
    def __str__(self):
        return f"Objetivos - {self.mes.strftime('%B %Y')}"


class NotaAnalisis(models.Model):
    """Notas y observaciones del análisis de rendimiento"""
    
    TIPO_CHOICES = [
        ('fortaleza', 'Fortaleza'),
        ('debilidad', 'Debilidad'),
        ('oportunidad', 'Oportunidad'),
        ('amenaza', 'Amenaza'),
        ('observacion', 'Observación General'),
        ('accion', 'Acción a Tomar'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    titulo = models.CharField(max_length=200, verbose_name='Título')
    contenido = models.TextField(verbose_name='Contenido')
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default='observacion',
        verbose_name='Tipo'
    )
    prioridad = models.CharField(
        max_length=20, choices=PRIORIDAD_CHOICES, default='media',
        verbose_name='Prioridad'
    )
    resuelta = models.BooleanField(default=False, verbose_name='Resuelta/Atendida')
    
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Creado por'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Nota de Análisis'
        verbose_name_plural = 'Notas de Análisis'
        ordering = ['-creado_en']
    
    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"
