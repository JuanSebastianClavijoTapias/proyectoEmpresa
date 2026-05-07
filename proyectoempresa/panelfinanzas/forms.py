from django import forms
from .models import Producto, Gasto


class ProductoForm(forms.ModelForm):
    """Formulario para crear/editar productos del catálogo"""
    
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 
            'precio_costo', 'precio_venta', 'es_precio_variable',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del producto (opcional)'
            }),
            'precio_costo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'es_precio_variable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class FiltroProductoForm(forms.Form):
    """Formulario para filtrar productos del catálogo"""
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar producto...'
        })
    )


class FiltroHistorialForm(forms.Form):
    """Formulario para filtrar el historial de entregas"""
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class GastoForm(forms.ModelForm):
    """Formulario para crear/editar gastos"""
    
    class Meta:
        model = Gasto
        fields = ['descripcion', 'monto', 'categoria', 'fecha', 'observaciones']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del gasto'
            }),
            'monto': forms.TextInput(attrs={
                'class': 'form-control precio-formato-co',
                'placeholder': '0',
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones (opcional)'
            }),
        }
