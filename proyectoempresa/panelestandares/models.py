from django.db import models
from django.contrib.auth.models import User


class CategoriaEstandar(models.Model):
    """Categorías para agrupar estándares (ej: Costura, Corte, Tapizado)"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Creado por'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría de Estándar'
        verbose_name_plural = 'Categorías de Estándares'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Estandar(models.Model):
    """Estándar de proceso de trabajo"""
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')
    categoria = models.ForeignKey(
        CategoriaEstandar, on_delete=models.CASCADE,
        related_name='estandares', verbose_name='Categoría'
    )
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Creado por'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estándar'
        verbose_name_plural = 'Estándares'
        ordering = ['categoria', 'titulo']

    def __str__(self):
        return f"{self.categoria} - {self.titulo}"
