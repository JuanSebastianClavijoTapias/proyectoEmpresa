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
                    'ganancia_unitaria', 'creado_por']
    list_filter = ['categoria']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['ganancia_unitaria', 'porcentaje_ganancia']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'descripcion', 'categoria')
        }),
        ('Precios', {
            'fields': ('precio_costo', 'precio_venta')
        }),
        ('Información de Ganancia (calculado)', {
            'fields': ('ganancia_unitaria', 'porcentaje_ganancia'),
            'classes': ('collapse',)
        }),
    )
    
    def ganancia_unitaria(self, obj):
        return f"${obj.ganancia_unitaria:,.2f}"
    ganancia_unitaria.short_description = 'Ganancia Unitaria'
    
    def porcentaje_ganancia(self, obj):
        return f"{obj.porcentaje_ganancia:.1f}%"
    porcentaje_ganancia.short_description = '% Ganancia'
