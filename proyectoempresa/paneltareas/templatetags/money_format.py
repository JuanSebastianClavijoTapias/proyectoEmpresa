"""
Filtro personalizado de Django para formatear valores monetarios.
Formatea números con separadores de miles según convención regional (latino).
Formato: 1.234.567,89
"""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def formato_dinero(value, decimales=0):
    """
    Formatea un valor numérico como dinero con separadores de miles.
    Usa el formato latino: 1.234.567,89
    
    Parámetros:
        value: Número a formatear (int, float, Decimal, string)
        decimales: Cantidad de decimales a mostrar (default: 0)
    
    Ejemplo en template:
        {{ tarea.precio_total|formato_dinero }}           --> 1.234.567
        {{ tarea.precio_total|formato_dinero:2 }}         --> 1.234.567,89
        {{ saldo_pendiente|formato_dinero:2 }}            --> 500.000,50
    """
    if value is None:
        return '0'
    
    try:
        # Convertir a Decimal para precisión
        if isinstance(value, str):
            value = Decimal(value.replace('.', '').replace(',', '.'))
        else:
            value = Decimal(str(value))
        
        # Redondear a la cantidad de decimales especificada
        decimales = int(decimales)
        value = round(value, decimales)
        
        # Convertir a string
        valor_str = f"{value:.{decimales}f}"
        
        # Separar parte entera y decimal
        if '.' in valor_str:
            partes = valor_str.split('.')
            parte_entera = partes[0]
            parte_decimal = partes[1]
        else:
            parte_entera = valor_str
            parte_decimal = None
        
        # Formatear parte entera con separadores de miles
        parte_entera_formateada = "{:,}".format(int(parte_entera)).replace(',', '.')
        
        # Reconstruir número
        if parte_decimal and decimales > 0:
            return f"{parte_entera_formateada},{parte_decimal}"
        else:
            return parte_entera_formateada
    
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return str(value)


@register.filter
def formato_moneda(value, decimales=2):
    """
    Alias más legible para formato_dinero.
    Alias para formato_dinero con 2 decimales por default.
    """
    return formato_dinero(value, decimales)


@register.filter
def formato_precio(value, decimales=0):
    """
    Alias para formatear precios sin decimales por default.
    """
    return formato_dinero(value, decimales)


@register.filter
def es_grande(value, limite=1000000):
    """
    Verifica si un número es mayor a 6 dígitos (>= 1.000.000).
    Retorna True/False para usarlo en condicionales de templates.
    
    Ejemplo:
        {% if precio|es_grande %}
            {{ precio|formato_dinero:2 }}
        {% endif %}
    """
    try:
        num = float(str(value).replace('.', '').replace(',', '.'))
        return num >= limite
    except (ValueError, TypeError):
        return False
