from django.contrib import admin
from .models import Trabajador, RegistroProductividad

@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'creado_en']
    list_filter = ['activo']
    search_fields = ['nombre']

@admin.register(RegistroProductividad)
class RegistroProductividadAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'trabajador', 'hora_inicio', 'hora_finalizacion', 'total_items', 'duracion']
    list_filter = ['fecha', 'trabajador']
    search_fields = ['trabajador__nombre']
    date_hierarchy = 'fecha'
    ordering = ['-fecha', '-hora_inicio']
    
    fieldsets = (
        ('Información General', {
            'fields': ('fecha', 'trabajador', 'hora_inicio', 'hora_finalizacion')
        }),
        ('Procesos Realizados', {
            'fields': ('cortado', 'marcado_piezas', 'costura', 'armado', 'instalacion', 'sillas_realizadas', 'tapizado_puertas', 'tapizado_techo')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
