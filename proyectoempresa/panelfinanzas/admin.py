from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario, Producto, Gasto
from core.permissions import ROLE_ADMINISTRADOR


# Extender la clase AdminSite default para agregar verificación de roles
original_has_permission = admin.site.__class__.has_permission


def role_based_has_permission(self, request):
    """
    Verifica que el usuario sea superusuario O tenga rol 'administrador'.
    
    Solo los usuarios con PerfilUsuario.rol = 'administrador' pueden acceder al panel de admin.
    Los superusuarios también tienen acceso automático.
    """
    # El usuario debe estar autenticado
    if not request.user.is_active or not request.user.is_authenticated:
        return False
    
    # Los superusuarios tienen acceso total
    if request.user.is_superuser:
        return True
    
    # Para usuarios normales, verificar que tengan rol administrador
    try:
        return request.user.perfil.rol == ROLE_ADMINISTRADOR
    except (PerfilUsuario.DoesNotExist, AttributeError):
        return False


# Aplicar el control de roles al admin site default
admin.site.has_permission = lambda request: role_based_has_permission(admin.site, request)
admin.site.site_header = "Administración - Cuir Tapicería"
admin.site.site_title = "Admin Cuir"
admin.site.index_title = "Panel de Administración"


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


# PerfilUsuario se gestiona como inline dentro del admin de User


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_costo', 'precio_venta', 
                    'ganancia_unitaria', 'creado_por']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['ganancia_unitaria', 'porcentaje_ganancia']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'descripcion')
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


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'monto', 'categoria', 'fecha', 'creado_por']
    list_filter = ['categoria', 'fecha']
    search_fields = ['descripcion', 'observaciones']
    date_hierarchy = 'fecha'
