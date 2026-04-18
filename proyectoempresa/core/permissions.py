"""
Sistema de control de acceso basado en roles (RBAC) para la aplicación.

Este módulo proporciona decoradores y mixins para restringir el acceso a vistas
según el rol del usuario (administrador, gerente, trabajador).

Roles y permisos:
- ADMINISTRADOR: Acceso completo a todos los módulos
- GERENTE: Acceso a tareas, productividad y finanzas (solo sección productos)
- TRABAJADOR: Acceso solo a tareas y productividad
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.views.generic import View


# =====================================================
# DECORADORES PARA FUNCIONES (function-based views)
# =====================================================

def require_role(*allowed_roles):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados.
    
    Uso:
        @require_role('administrador', 'gerente')
        def mi_vista(request):
            pass
    
    Parámetros:
        allowed_roles: Lista de roles permitidos
    
    Si el usuario no está autenticado: redirige a login
    Si el usuario no tiene el rol requerido: muestra 403 Forbidden
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Si es superusuario, permitir siempre
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si el usuario tiene perfil
            try:
                perfil = request.user.perfil
            except Exception:
                messages.error(request, 'Tu usuario no tiene un perfil configurado.')
                return redirect('login')
            
            # Verificar si el rol está permitido
            if perfil.rol in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Acceso denegado
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        
        return wrapper
    return decorator


def require_administrador(view_func):
    """
    Decorador que requiere rol de ADMINISTRADOR.
    
    Uso:
        @require_administrador
        def vista_admin(request):
            pass
    
    Solo los superusuarios y usuarios con rol 'administrador' pueden acceder.
    """
    return require_role('administrador')(view_func)


def require_not_trabajador(view_func):
    """
    Decorador que bloquea a usuarios con rol TRABAJADOR.
    
    Uso:
        @require_not_trabajador
        def vista_gerente_o_admin(request):
            pass
    
    Permite: administrador, gerente
    Bloquea: trabajador
    """
    return require_role('administrador', 'gerente')(view_func)


def require_administrador_o_gerente(view_func):
    """
    Decorador que requiere rol de ADMINISTRADOR o GERENTE.
    
    Uso:
        @require_administrador_o_gerente
        def vista_finanzas(request):
            pass
    
    Alias para @require_not_trabajador.
    """
    return require_role('administrador', 'gerente')(view_func)


def require_gerente(view_func):
    """
    Decorador que requiere rol de GERENTE.
    
    Uso:
        @require_gerente
        def vista_gerente(request):
            pass
    
    Solo administrador y gerente pueden acceder (no trabajador).
    """
    return require_role('administrador', 'gerente')(view_func)


# =====================================================
# MIXINS PARA VISTAS BASADAS EN CLASES (class-based views)
# =====================================================

class RoleRequiredMixin:
    """
    Mixin para vistas basadas en clases que requieren un rol específico.
    
    Uso:
        class MiVista(RoleRequiredMixin, View):
            required_roles = ['administrador', 'gerente']
            
            def get(self, request):
                pass
    
    Subclases deben definir 'required_roles' como lista de roles permitidos.
    """
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        # Si es superusuario, permitir
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Verificar autenticación
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión.')
            return redirect('login')
        
        # Verificar perfil
        try:
            perfil = request.user.perfil
        except Exception:
            messages.error(request, 'Tu usuario no tiene un perfil configurado.')
            return redirect('login')
        
        # Verificar rol
        if perfil.rol not in self.required_roles:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class AdministradorRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de ADMINISTRADOR."""
    required_roles = ['administrador']


class NotTrabajadorMixin(RoleRequiredMixin):
    """Mixin que bloquea TRABAJADOR (permite ADMINISTRADOR y GERENTE)."""
    required_roles = ['administrador', 'gerente']


class AdministradorOGerenteMixin(RoleRequiredMixin):
    """Mixin que requiere ADMINISTRADOR o GERENTE."""
    required_roles = ['administrador', 'gerente']


class GerenteRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de GERENTE (incluyendo ADMINISTRADOR)."""
    required_roles = ['administrador', 'gerente']


# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def user_has_role(user, *roles):
    """
    Verifica si un usuario tiene uno de los roles especificados.
    
    Parámetros:
        user: Objeto User de Django
        roles: Roles a verificar
    
    Retorna:
        True si el usuario tiene uno de los roles (o es superusuario)
        False en caso contrario
    """
    if user.is_superuser:
        return True
    
    try:
        perfil = user.perfil
        return perfil.rol in roles
    except Exception:
        return False


def user_can_access_finanzas(user):
    """
    Verifica si un usuario puede acceder al módulo de finanzas.
    
    Acceso permitido para: administrador, gerente
    Bloqueado para: trabajador
    """
    return user_has_role(user, 'administrador', 'gerente')


def user_can_access_productos(user):
    """
    Verifica si un usuario puede acceder a la sección de PRODUCTOS en finanzas.
    
    Acceso permitido para: administrador, gerente
    Bloqueado para: trabajador
    """
    return user_has_role(user, 'administrador', 'gerente')


def user_can_access_gastos(user):
    """
    Verifica si un usuario puede acceder a la sección de GASTOS en finanzas.
    
    Acceso permitido para: administrador (solo)
    Bloqueado para: gerente, trabajador
    """
    return user_has_role(user, 'administrador')


def user_can_access_analisis(user):
    """
    Verifica si un usuario puede acceder al módulo de análisis.
    
    Acceso permitido para: administrador (solo)
    Bloqueado para: gerente, trabajador
    
    Nota: Análisis de trabajadores y objetivos son accesibles para todos.
    Solo el dashboard y análisis financiero requieren administrador.
    """
    return user_has_role(user, 'administrador')


def user_can_access_estandares(user):
    """
    Verifica si un usuario puede acceder al módulo de estándares.
    
    Acceso permitido para: administrador (solo)
    Bloqueado para: gerente, trabajador
    """
    return user_has_role(user, 'administrador')


# =====================================================
# CONSTANTES DE ROLES
# =====================================================

ROLE_ADMINISTRADOR = 'administrador'
ROLE_GERENTE = 'gerente'
ROLE_TRABAJADOR = 'trabajador'

ROLES = {
    ROLE_ADMINISTRADOR: 'Administrador',
    ROLE_GERENTE: 'Gerente',
    ROLE_TRABAJADOR: 'Trabajador',
}
