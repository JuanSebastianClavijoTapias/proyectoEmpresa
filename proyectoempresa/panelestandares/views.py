from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count

from .models import CategoriaEstandar, Estandar
from .forms import CategoriaEstandarForm, EstandarForm
from core.permissions import require_administrador


# =============================================
# ESTÁNDARES
# =============================================

@require_administrador
def lista_estandares(request):
    """Lista todos los estándares agrupados por categoría"""
    categorias = CategoriaEstandar.objects.prefetch_related('estandares').all()
    return render(request, 'panelestandares/lista.html', {
        'categorias': categorias,
    })


@require_administrador
def crear_estandar(request):
    if request.method == 'POST':
        form = EstandarForm(request.POST)
        if form.is_valid():
            estandar = form.save(commit=False)
            estandar.creado_por = request.user
            estandar.save()
            messages.success(request, 'Estándar creado exitosamente.')
            return redirect('estandares:lista')
    else:
        form = EstandarForm()
    return render(request, 'panelestandares/crear.html', {'form': form})


@require_administrador
def editar_estandar(request, pk):
    estandar = get_object_or_404(Estandar, pk=pk)
    if request.method == 'POST':
        form = EstandarForm(request.POST, instance=estandar)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estándar actualizado exitosamente.')
            return redirect('estandares:lista')
    else:
        form = EstandarForm(instance=estandar)
    return render(request, 'panelestandares/editar.html', {'form': form, 'estandar': estandar})


@require_administrador
def eliminar_estandar(request, pk):
    estandar = get_object_or_404(Estandar, pk=pk)
    if request.method == 'POST':
        estandar.delete()
        messages.success(request, 'Estándar eliminado exitosamente.')
        return redirect('estandares:lista')
    return render(request, 'panelestandares/eliminar.html', {'estandar': estandar})


# =============================================
# CATEGORÍAS
# =============================================

@require_administrador
def lista_categorias(request):
    categorias = CategoriaEstandar.objects.annotate(
        total=Count('estandares')
    )
    return render(request, 'panelestandares/categorias/lista.html', {
        'categorias': categorias,
    })


@require_administrador
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaEstandarForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.creado_por = request.user
            categoria.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('estandares:lista_categorias')
    else:
        form = CategoriaEstandarForm()
    return render(request, 'panelestandares/categorias/crear.html', {'form': form})


@require_administrador
def editar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaEstandar, pk=pk)
    if request.method == 'POST':
        form = CategoriaEstandarForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('estandares:lista_categorias')
    else:
        form = CategoriaEstandarForm(instance=categoria)
    return render(request, 'panelestandares/categorias/editar.html', {'form': form, 'categoria': categoria})


@require_administrador
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaEstandar, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('estandares:lista_categorias')
    return render(request, 'panelestandares/categorias/eliminar.html', {'categoria': categoria})
