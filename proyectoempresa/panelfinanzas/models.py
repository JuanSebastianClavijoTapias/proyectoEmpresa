from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    """Modelo para extender el usuario con rol"""
    
    ROL_CHOICES = [
        ('jefe', 'Jefe'),
        ('trabajador', 'Trabajador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='trabajador', verbose_name='Rol')
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"
    
    @property
    def es_jefe(self):
        return self.rol == 'jefe'
    
    @property
    def es_trabajador(self):
        return self.rol == 'trabajador'


# Señales para crear perfil automáticamente
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


class CategoriaProducto(models.Model):
    """Categorías para organizar productos"""
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    
    class Meta:
        verbose_name = 'Categoría de Producto'
        verbose_name_plural = 'Categorías de Productos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Catálogo de productos con sus precios"""
    
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Producto')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    categoria = models.ForeignKey(
        CategoriaProducto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='productos',
        verbose_name='Categoría'
    )
    
    # Precios
    precio_costo = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name='Precio de Costo',
        help_text='Lo que nos cuesta el producto'
    )
    precio_venta = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name='Precio de Venta',
        help_text='A cuánto se vende al cliente'
    )
    
    # Metadatos
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='productos_creados',
        verbose_name='Registrado por'
    )
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_venta:,.0f}"
    
    @property
    def ganancia_unitaria(self):
        """Calcula la ganancia por unidad"""
        return self.precio_venta - self.precio_costo
    
    @property
    def porcentaje_ganancia(self):
        """Calcula el porcentaje de ganancia"""
        if self.precio_costo > 0:
            return ((self.precio_venta - self.precio_costo) / self.precio_costo) * 100
        return 0


class Gasto(models.Model):
    """Modelo para registrar gastos del negocio"""
    
    CATEGORIA_CHOICES = [
        ('servicios', 'Servicios (Luz, Agua, Internet)'),
        ('alquiler', 'Alquiler / Arriendo'),
        ('materiales', 'Materiales e Insumos'),
        ('herramientas', 'Herramientas y Equipos'),
        ('transporte', 'Transporte'),
        ('salarios', 'Salarios / Nómina'),
        ('impuestos', 'Impuestos'),
        ('mantenimiento', 'Mantenimiento'),
        ('publicidad', 'Publicidad / Marketing'),
        ('otro', 'Otro'),
    ]
    
    descripcion = models.CharField(max_length=300, verbose_name='Descripción del Gasto')
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto')
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, default='otro', verbose_name='Categoría')
    fecha = models.DateField(verbose_name='Fecha del Gasto')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='gastos_creados',
        verbose_name='Registrado por'
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    
    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.descripcion} - ${self.monto:,.0f} ({self.get_categoria_display()})"
