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
    
    # Gastos
    path('gastos/', views.lista_gastos, name='lista_gastos'),
    path('gastos/crear/', views.crear_gasto, name='crear_gasto'),
    path('gastos/<int:pk>/editar/', views.editar_gasto, name='editar_gasto'),
    path('gastos/<int:pk>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),
]
