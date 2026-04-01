from django.contrib import admin
from .models import ObjetivoMensual, NotaAnalisis


@admin.register(ObjetivoMensual)
class ObjetivoMensualAdmin(admin.ModelAdmin):
    list_display = ['mes', 'meta_ingresos', 'meta_ganancia', 'meta_tareas_completadas', 'creado_por']
    list_filter = ['mes']
    search_fields = ['notas']


@admin.register(NotaAnalisis)
class NotaAnalisisAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'prioridad', 'resuelta', 'creado_por', 'creado_en']
    list_filter = ['tipo', 'prioridad', 'resuelta']
    search_fields = ['titulo', 'contenido']
