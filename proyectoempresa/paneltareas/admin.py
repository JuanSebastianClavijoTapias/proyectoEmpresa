from django.contrib import admin
from .models import Cliente, TareaPlanificada

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'creado_en']
    search_fields = ['nombre', 'telefono']
    ordering = ['nombre']

@admin.register(TareaPlanificada)
class TareaPlanificadaAdmin(admin.ModelAdmin):
    list_display = ['placa', 'nombre_cliente', 'fecha_ingreso', 'fecha_entrega', 'estado', 'prioridad']
    list_filter = ['estado', 'prioridad', 'fecha_entrega']
    search_fields = ['nombre_cliente', 'placa', 'telefono_cliente', 'descripcion_trabajo']
    date_hierarchy = 'fecha_ingreso'
    ordering = ['fecha_entrega', '-prioridad']
    list_editable = ['estado', 'prioridad']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre_cliente', 'telefono_cliente')
        }),
        ('Vehículo', {
            'fields': ('placa',)
        }),
        ('Detalles del Trabajo', {
            'fields': ('descripcion_trabajo',)
        }),
        ('Fechas y Estado', {
            'fields': ('fecha_ingreso', 'fecha_entrega', 'estado', 'prioridad')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
