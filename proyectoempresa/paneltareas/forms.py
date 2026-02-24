from django import forms
from .models import TareaPlanificada, Cliente, ImagenTarea


class TareaPlanificadaForm(forms.ModelForm):
    class Meta:
        model = TareaPlanificada
        fields = [
            'nombre_cliente', 'telefono_cliente',
            'placa',
            'descripcion_trabajo',
            'fecha_ingreso', 'fecha_entrega', 'estado', 'prioridad',
            'observaciones'
        ]
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'telefono_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de contacto'}),
            'placa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABC-123'}),
            'descripcion_trabajo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Qué se le debe hacer al vehículo...'}),
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones adicionales...'}),
        }


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
        }


class ImagenTareaForm(forms.ModelForm):
    """Formulario para subir imágenes a las tareas"""
    class Meta:
        model = ImagenTarea
        fields = ['imagen', 'descripcion']
        widgets = {
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',  # Permite seleccionar solo imágenes
                'capture': 'environment',  # Habilita cámara en móviles
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la imagen (opcional)',
                'maxlength': '200'
            }),
        }
