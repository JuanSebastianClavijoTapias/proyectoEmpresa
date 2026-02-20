from django.urls import path
from . import views

app_name = 'productividad'

urlpatterns = [
    # Registros de productividad
    path('', views.lista_productividad, name='lista'),
    path('crear/', views.crear_productividad, name='crear'),
    path('<int:pk>/', views.detalle_productividad, name='detalle'),
    path('<int:pk>/editar/', views.editar_productividad, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_productividad, name='eliminar'),
    
    # Trabajadores
    path('trabajadores/', views.lista_trabajadores, name='lista_trabajadores'),
    path('trabajadores/crear/', views.crear_trabajador, name='crear_trabajador'),
    path('trabajadores/<int:pk>/', views.detalle_trabajador, name='detalle_trabajador'),
    path('trabajadores/<int:pk>/editar/', views.editar_trabajador, name='editar_trabajador'),
]
