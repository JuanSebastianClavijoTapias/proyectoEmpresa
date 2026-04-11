from django.urls import path
from . import views_trabajador

app_name = 'trabajador'

urlpatterns = [
    path('login/', views_trabajador.login_trabajador, name='login'),
    path('logout/', views_trabajador.logout_trabajador, name='logout'),
    path('dashboard/', views_trabajador.dashboard_trabajador, name='dashboard'),
    path('productividad/', views_trabajador.mi_productividad, name='productividad'),
    path('registrar/', views_trabajador.registrar_productividad, name='registrar'),
]
