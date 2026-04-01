from django.urls import path
from . import views

app_name = 'finanzas'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Catálogo de Productos
    path('', views.lista_productos, name='lista'),
    path('crear/', views.crear_producto, name='crear'),
    path('<int:pk>/', views.detalle_producto, name='detalle'),
    path('<int:pk>/editar/', views.editar_producto, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_producto, name='eliminar'),
    
    # Historial de Entregas
    path('historial/', views.historial_entregas, name='historial'),
    
    # Reportes
    path('reporte/', views.reporte_finanzas, name='reporte'),
    
    # Categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:pk>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
]
