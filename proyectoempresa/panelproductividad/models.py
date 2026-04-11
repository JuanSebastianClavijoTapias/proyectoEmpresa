from django.db import models
from django.contrib.auth.models import User


class Trabajador(models.Model):
    """Modelo para los trabajadores del taller"""
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trabajador', null=True, blank=True, verbose_name='Usuario')
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class RegistroProductividad(models.Model):
    """Modelo para registrar la productividad diaria por trabajador"""
    
    fecha = models.DateField(verbose_name='Fecha')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='registros', verbose_name='Trabajador', null=True, blank=True)
    hora_inicio = models.TimeField(verbose_name='Hora de Inicio')
    hora_finalizacion = models.TimeField(verbose_name='Hora de Finalización')
    
    # Procesos estandarizados con cantidades
    cortado = models.PositiveIntegerField(default=0, verbose_name='Cortado')
    marcado_piezas = models.PositiveIntegerField(default=0, verbose_name='Marcado de Piezas')
    costura = models.PositiveIntegerField(default=0, verbose_name='Costura')
    armado = models.PositiveIntegerField(default=0, verbose_name='Armado')
    instalacion = models.PositiveIntegerField(default=0, verbose_name='Instalación')
    sillas_realizadas = models.PositiveIntegerField(default=0, verbose_name='Sillas Realizadas')
    tapizado_puertas = models.PositiveIntegerField(default=0, verbose_name='Tapizado Puertas')
    tapizado_techo = models.PositiveIntegerField(default=0, verbose_name='Tapizado Techo')
    
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    
    class Meta:
        verbose_name = 'Registro de Productividad'
        verbose_name_plural = 'Registros de Productividad'
        ordering = ['-fecha', '-hora_inicio']
    
    def __str__(self):
        return f"{self.fecha} - {self.trabajador}"
    
    @property
    def duracion(self):
        """Calcula la duración del trabajo"""
        from datetime import datetime, timedelta
        inicio = datetime.combine(self.fecha, self.hora_inicio)
        fin = datetime.combine(self.fecha, self.hora_finalizacion)
        if fin < inicio:
            fin += timedelta(days=1)
        diferencia = fin - inicio
        horas = diferencia.seconds // 3600
        minutos = (diferencia.seconds % 3600) // 60
        return f"{horas}h {minutos}m"
    
    @property
    def total_items(self):
        """Total de items procesados"""
        return (self.cortado + self.marcado_piezas + self.costura + 
                self.armado + self.instalacion + self.sillas_realizadas +
                self.tapizado_puertas + self.tapizado_techo)
