from django.contrib import admin
from .models import Cliente, TareaPlanificada, ProductoTarea, ImagenTarea, NotaTrabajo

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'creado_en']
    search_fields = ['nombre', 'telefono']
    ordering = ['nombre']


class ProductoTareaInline(admin.TabularInline):
    model = ProductoTarea
    extra = 1
    readonly_fields = ['nombre_producto', 'precio_costo', 'precio_venta']
    fields = ['producto', 'nombre_producto', 'cantidad', 'precio_costo', 'precio_venta']


@admin.register(TareaPlanificada)
class TareaPlanificadaAdmin(admin.ModelAdmin):
    list_display = ['placa', 'nombre_cliente', 'fecha_ingreso', 'fecha_entrega', 'estado', 'prioridad', 'monto_abonado']
    list_filter = ['estado', 'prioridad', 'fecha_entrega']
    search_fields = ['nombre_cliente', 'placa', 'telefono_cliente', 'descripcion_trabajo']
    date_hierarchy = 'fecha_ingreso'
    ordering = ['fecha_entrega', '-prioridad']
    list_editable = ['estado', 'prioridad']
    inlines = [ProductoTareaInline]
    
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
        ('Finanzas (Solo Administración)', {
            'fields': ('monto_abonado',),
            'description': 'Monto abonado por el cliente. Este campo NO es visible para los trabajadores.'
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductoTarea)
class ProductoTareaAdmin(admin.ModelAdmin):
    list_display = ['nombre_producto', 'tarea', 'cantidad', 'precio_costo', 'precio_venta', 'fecha_registro']
    list_filter = ['fecha_registro']
    search_fields = ['nombre_producto', 'tarea__nombre_cliente', 'tarea__placa']
    date_hierarchy = 'fecha_registro'


@admin.register(ImagenTarea)
class ImagenTareaAdmin(admin.ModelAdmin):
    list_display = ['id', 'tarea', 'producto_tarea', 'descripcion', 'fecha_subida', 'eliminada']
    list_filter = ['fecha_subida', 'eliminada']
    search_fields = ['tarea__nombre_cliente', 'tarea__placa', 'producto_tarea__nombre_producto', 'descripcion']
    autocomplete_fields = ['tarea', 'producto_tarea']


@admin.register(NotaTrabajo)
class NotaTrabajoAdmin(admin.ModelAdmin):
    list_display = ['id', 'contenido_corto', 'creado_por', 'creado_en', 'tomada']
    list_filter = ['tomada', 'creado_en']
    search_fields = ['contenido']

    def contenido_corto(self, obj):
        return obj.contenido[:80]
    contenido_corto.short_description = 'Contenido'
