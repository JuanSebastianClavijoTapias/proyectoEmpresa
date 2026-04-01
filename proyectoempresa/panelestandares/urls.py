from django.urls import path
from . import views

app_name = 'estandares'

urlpatterns = [
    # Estándares
    path('', views.lista_estandares, name='lista'),
    path('crear/', views.crear_estandar, name='crear'),
    path('<int:pk>/editar/', views.editar_estandar, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_estandar, name='eliminar'),

    # Categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:pk>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
]
