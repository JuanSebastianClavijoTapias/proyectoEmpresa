from django.urls import path
from . import views

app_name = 'analisis'

urlpatterns = [
    # Dashboard principal de KPIs
    path('', views.dashboard_analisis, name='dashboard'),
    
    # Análisis de rendimiento por trabajador
    path('trabajadores/', views.analisis_trabajadores, name='trabajadores'),
    
    # Análisis financiero detallado
    path('financiero/', views.analisis_financiero, name='financiero'),
    
    # Objetivos mensuales
    path('objetivos/', views.lista_objetivos, name='lista_objetivos'),
    path('objetivos/crear/', views.crear_objetivo, name='crear_objetivo'),
    path('objetivos/<int:pk>/editar/', views.editar_objetivo, name='editar_objetivo'),
    path('objetivos/<int:pk>/eliminar/', views.eliminar_objetivo, name='eliminar_objetivo'),
    
    # Notas de análisis
    path('notas/', views.lista_notas, name='lista_notas'),
    path('notas/crear/', views.crear_nota, name='crear_nota'),
    path('notas/<int:pk>/resolver/', views.resolver_nota, name='resolver_nota'),
    path('notas/<int:pk>/eliminar/', views.eliminar_nota, name='eliminar_nota'),
]
