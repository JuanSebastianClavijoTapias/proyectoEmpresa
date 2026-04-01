from django import forms
from .models import ObjetivoMensual, NotaAnalisis


class FiltroAnalisisForm(forms.Form):
    """Formulario para filtrar el período del análisis"""
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Desde'
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Hasta'
    )


class ObjetivoMensualForm(forms.ModelForm):
    """Formulario para crear/editar objetivos mensuales"""
    
    class Meta:
        model = ObjetivoMensual
        fields = [
            'mes', 'meta_ingresos', 'meta_ganancia',
            'meta_tareas_completadas', 'meta_clientes_nuevos',
            'meta_items_producidos', 'notas'
        ]
        widgets = {
            'mes': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'meta_ingresos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'meta_ganancia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'meta_tareas_completadas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'meta_clientes_nuevos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'meta_items_producidos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


class NotaAnalisisForm(forms.ModelForm):
    """Formulario para crear notas de análisis"""
    
    class Meta:
        model = NotaAnalisis
        fields = ['titulo', 'contenido', 'tipo', 'prioridad']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
        }
