from django.urls import path
from . import views
from . import views_kanban

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
    path('<int:pk>/imagen/<int:imagen_pk>/eliminar/', views.eliminar_imagen, name='eliminar_imagen'),
    path('<int:pk>/abonar/', views.abonar_tarea, name='abonar'),
    path('<int:pk>/completar-pago/', views.completar_pago_tarea, name='completar_pago'),
    
    # Kanban Board
    path('kanban/', views_kanban.kanban_board, name='kanban'),
    path('api/kanban/tareas/', views_kanban.get_tareas_kanban, name='api_get_tareas_kanban'),
    path('api/kanban/tareas/<int:tarea_id>/estado/', views_kanban.actualizar_estado_tarea, name='api_actualizar_estado_tarea'),
    path('api/kanban/reordenar/', views_kanban.reordenar_tareas, name='api_reordenar_tareas'),
    
    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
]
