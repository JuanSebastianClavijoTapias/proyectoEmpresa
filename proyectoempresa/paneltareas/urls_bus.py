from django.urls import path
from . import views_bus
from . import views  # para detalle, abonar, completar_pago, eliminar_imagen

app_name = 'bus'

urlpatterns = [
    # Lista y CRUD
    path('', views_bus.lista_tareas_bus, name='lista'),
    path('crear/', views_bus.crear_tarea_bus, name='crear'),
    path('<int:pk>/editar/', views_bus.editar_tarea_bus, name='editar'),
    path('<int:pk>/eliminar/', views_bus.eliminar_tarea_bus, name='eliminar'),
    path('<int:pk>/estado/<str:estado>/', views_bus.cambiar_estado_bus, name='cambiar_estado'),

    # Compartidos con tareas (detalle, pagos, imágenes)
    path('<int:pk>/', views.detalle_tarea, name='detalle'),
    path('<int:pk>/abonar/', views.abonar_tarea, name='abonar'),
    path('<int:pk>/completar-pago/', views.completar_pago_tarea, name='completar_pago'),
    path('<int:pk>/imagen/<int:imagen_pk>/eliminar/', views.eliminar_imagen, name='eliminar_imagen'),
]
