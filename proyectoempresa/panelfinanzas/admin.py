from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario, Producto, CategoriaProducto


class PerfilUsuarioInline(admin.StackedInline):
    """Inline para mostrar el perfil dentro del admin de usuario"""
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'


class UserAdmin(BaseUserAdmin):
    """Admin personalizado para User que incluye el perfil"""
    inlines = [PerfilUsuarioInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_rol', 'is_active']
    
    def get_rol(self, obj):
        try:
            return obj.perfil.get_rol_display()
        except PerfilUsuario.DoesNotExist:
            return '-'
    get_rol.short_description = 'Rol'


# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'rol']
    list_filter = ['rol']
    search_fields = ['user__username', 'user__email']


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio_costo', 'precio_venta', 
                    'ganancia_unitaria', 'cantidad', 'fecha', 'creado_por']
    list_filter = ['categoria', 'fecha']
    search_fields = ['nombre', 'cliente_nombre', 'descripcion']
    date_hierarchy = 'fecha'
    readonly_fields = ['ganancia_unitaria', 'ganancia_total', 'porcentaje_ganancia']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'descripcion', 'categoria')
        }),
        ('Precios y Cantidades', {
            'fields': ('precio_costo', 'precio_venta', 'cantidad')
        }),
        ('Información de Ganancia (calculado)', {
            'fields': ('ganancia_unitaria', 'ganancia_total', 'porcentaje_ganancia'),
            'classes': ('collapse',)
        }),
        ('Cliente y Fecha', {
            'fields': ('cliente_nombre', 'fecha')
        }),
    )
    
    def ganancia_unitaria(self, obj):
        return f"${obj.ganancia_unitaria:,.2f}"
    ganancia_unitaria.short_description = 'Ganancia Unitaria'
    
    def ganancia_total(self, obj):
        return f"${obj.ganancia_total:,.2f}"
    ganancia_total.short_description = 'Ganancia Total'
    
    def porcentaje_ganancia(self, obj):
        return f"{obj.porcentaje_ganancia:.1f}%"
    porcentaje_ganancia.short_description = '% Ganancia'
