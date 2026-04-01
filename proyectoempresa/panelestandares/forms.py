from django import forms
from .models import CategoriaEstandar, Estandar


class CategoriaEstandarForm(forms.ModelForm):
    class Meta:
        model = CategoriaEstandar
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EstandarForm(forms.ModelForm):
    class Meta:
        model = Estandar
        fields = ['titulo', 'descripcion', 'categoria']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }
