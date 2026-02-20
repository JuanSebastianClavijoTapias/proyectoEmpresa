from django.urls import path
from . import views

app_name = 'tareas'

urlpatterns = [
    # Tareas
    path('', views.lista_tareas, name='lista'),
    path('calendario/', views.calendario_tareas, name='calendario'),
    path('crear/', views.crear_tarea, name='crear'),
    path('<int:pk>/', views.detalle_tarea, name='detalle'),
    path('<int:pk>/editar/', views.editar_tarea, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_tarea, name='eliminar'),
    path('<int:pk>/estado/<str:estado>/', views.cambiar_estado_tarea, name='cambiar_estado'),
    
    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
]
