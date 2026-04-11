#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoempresa.settings')
django.setup()

from django.contrib.auth.models import User

print("Reseteando contraseñas de trabajadores a: 12345678\n")

trabajadores_usuarios = [
    'camilo_perez',
    'clavijo',
    'samuel_pineres',
    'prueba',
    'prueba1',
]

for username in trabajadores_usuarios:
    try:
        user = User.objects.get(username=username)
        user.set_password('12345678')
        user.save()
        print(f"✓ {username} → contraseña: 12345678")
    except User.DoesNotExist:
        print(f"✗ {username} no encontrado")

print("\n¡Ahora puedes ingresar con contraseña: 12345678")
