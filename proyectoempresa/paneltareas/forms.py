from django import forms
from django.forms import inlineformset_factory
from .models import TareaPlanificada, Cliente, ImagenTarea, ProductoTarea
from panelfinanzas.models import Producto


class TareaPlanificadaForm(forms.ModelForm):
    class Meta:
        model = TareaPlanificada
        fields = [
            'nombre_cliente', 'telefono_cliente', 'placa',
            'descripcion_trabajo',
            'fecha_ingreso', 'fecha_entrega', 'estado', 'prioridad',
            'observaciones', 'monto_abonado'
        ]
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'telefono_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de contacto'}),
            'placa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Placa del vehículo (opcional)', 'autocomplete': 'off'}),
            'descripcion_trabajo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Qué se le debe hacer...'}),
            'fecha_ingreso': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_entrega': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones adicionales...'}),
            'monto_abonado': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
        }


class TareaPlanificadaFormJefe(TareaPlanificadaForm):
    """Formulario extendido para jefes que incluye monto abonado"""
    class Meta(TareaPlanificadaForm.Meta):
        fields = TareaPlanificadaForm.Meta.fields + ['monto_abonado']
        widgets = {
            **TareaPlanificadaForm.Meta.widgets,
            'monto_abonado': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
        }


class ProductoTareaForm(forms.ModelForm):
    """Formulario para agregar productos a una tarea"""
    nombre_producto_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control producto-nombre-input',
            'placeholder': 'Escriba o seleccione un producto',
            'autocomplete': 'off',
        }),
        label='Producto',
    )
    precio_cobrado = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control precio-cobrado-input',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Precio cobrado',
        }),
        label='Precio',
    )

    class Meta:
        model = ProductoTarea
        fields = ['producto', 'placa', 'cantidad']
        widgets = {
            'producto': forms.HiddenInput(attrs={'class': 'producto-id-hidden'}),
            'placa': forms.TextInput(attrs={'class': 'form-control placa-input', 'placeholder': 'Placa', 'autocomplete': 'off'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.all()
        self.fields['producto'].required = False
        # Pre-fill nombre_producto_input and precio_cobrado if editing an existing ProductoTarea
        if self.instance and self.instance.pk:
            self.fields['nombre_producto_input'].initial = self.instance.nombre_producto
            self.fields['precio_cobrado'].initial = self.instance.precio_venta


ProductoTareaFormSet = inlineformset_factory(
    TareaPlanificada,
    ProductoTarea,
    form=ProductoTareaForm,
    extra=1,
    can_delete=True,
    fields=['producto', 'placa', 'cantidad'],
)


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo (opcional)'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección (opcional)'}),
        }


class AbonarForm(forms.Form):
    """Formulario para abonar dinero a una tarea"""
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01',
        }),
        label='Monto a abonar',
    )


class ImagenTareaForm(forms.ModelForm):
    """Formulario para subir imágenes a las tareas"""
    producto_tarea = forms.ModelChoiceField(
        queryset=ProductoTarea.objects.none(),
        required=True,
        label='Producto',
        empty_label='Seleccione el producto',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
    )

    def __init__(self, *args, tarea=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = ProductoTarea.objects.none()
        if tarea is not None:
            queryset = tarea.productos_tarea.all()
        self.fields['producto_tarea'].queryset = queryset
        self.fields['producto_tarea'].label_from_instance = lambda producto_tarea: (
            f"{producto_tarea.nombre_producto} x{producto_tarea.cantidad}"
        )

    class Meta:
        model = ImagenTarea
        fields = ['producto_tarea', 'imagen', 'descripcion']
        widgets = {
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la imagen (opcional)',
                'maxlength': '200'
            }),
        }
