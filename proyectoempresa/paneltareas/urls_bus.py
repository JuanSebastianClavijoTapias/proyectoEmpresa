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

    # Papelera de imágenes
    path('papelera/', views.papelera_imagenes, name='papelera'),
    path('papelera/<int:imagen_pk>/restaurar/', views.restaurar_imagen, name='restaurar_imagen'),
    path('papelera/<int:imagen_pk>/eliminar/', views.eliminar_permanente_imagen, name='eliminar_permanente_imagen'),
    path('papelera/vaciar/', views.vaciar_papelera, name='vaciar_papelera'),

    # Anotación de imágenes
    path('imagen/<int:imagen_pk>/anotar/', views.anotar_imagen, name='anotar_imagen'),

    # Notas de trabajo
    path('notas/crear/', views.crear_nota_trabajo, name='crear_nota'),
    path('notas/<int:nota_pk>/tomada/', views.toggle_tomada_nota, name='toggle_tomada_nota'),
    path('notas/<int:nota_pk>/eliminar/', views.eliminar_nota_trabajo, name='eliminar_nota'),

    # Exportar y borrar masivo
    path('exportar-csv/', views.exportar_tareas_csv, name='exportar_csv'),
    path('borrar-seleccionadas/', views.borrar_seleccionadas, name='borrar_seleccionadas'),
]
