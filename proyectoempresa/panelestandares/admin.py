from django.contrib import admin
from .models import CategoriaEstandar, Estandar


@admin.register(CategoriaEstandar)
class CategoriaEstandarAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'creado_por', 'creado_en']
    search_fields = ['nombre']


@admin.register(Estandar)
class EstandarAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'creado_por', 'creado_en']
    list_filter = ['categoria']
    search_fields = ['titulo', 'descripcion']
