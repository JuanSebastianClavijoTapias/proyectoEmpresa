from django import forms
from .models import Trabajador, RegistroProductividad


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del trabajador'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RegistroProductividadForm(forms.ModelForm):
    class Meta:
        model = RegistroProductividad
        fields = [
            'fecha', 'trabajador', 'hora_inicio', 'hora_finalizacion',
            'cortado', 'marcado_piezas', 'costura', 'armado', 
            'instalacion', 'sillas_realizadas', 'tapizado_puertas', 'tapizado_techo',
            'observaciones'
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'trabajador': forms.Select(attrs={'class': 'form-select'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_finalizacion': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'cortado': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'marcado_piezas': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'costura': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'armado': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'instalacion': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'sillas_realizadas': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'tapizado_puertas': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'tapizado_techo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones adicionales...'}),
        }
