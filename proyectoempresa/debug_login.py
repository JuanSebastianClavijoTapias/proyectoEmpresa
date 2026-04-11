#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoempresa.settings')
django.setup()

from django.contrib.auth.models import User
from panelproductividad.models import Trabajador

print("=" * 60)
print("DEBUG: Verificando usuarios y trabajadores")
print("=" * 60)

# Todos los usuarios
print("\n1️⃣ USUARIOS EN EL SISTEMA:")
usuarios = User.objects.all()
for u in usuarios:
    print(f"   ✓ {u.username}")
    print(f"     - is_active: {u.is_active}")
    print(f"     - is_staff: {u.is_staff}")
    print(f"     - is_superuser: {u.is_superuser}")
    print()

# Trabajadores con usuario
print("\n2️⃣ TRABAJADORES CON USUARIO ASOCIADO:")
for t in Trabajador.objects.filter(usuario__isnull=False):
    print(f"   ✓ {t.nombre} → {t.usuario.username}")

# Trabajadores sin usuario
print("\n3️⃣ TRABAJADORES SIN USUARIO:")
for t in Trabajador.objects.filter(usuario__isnull=True):
    print(f"   ✗ {t.nombre}")

# Probar autenticación
print("\n4️⃣ PRUEBA DE AUTENTICACIÓN:")
from django.contrib.auth import authenticate

for u in User.objects.all():
    print(f"\n   Probando con usuario: {u.username}")
    
    # Intentar autenticarse
    user = authenticate(username=u.username, password='test123')
    if user:
        print(f"   ✓ Autenticación exitosa con 'test123'")
    else:
        print(f"   ✗ Autenticación fallida con 'test123'")
    
    # Verificar si tiene trabajador asociado
    if hasattr(u, 'trabajador'):
        print(f"   ✓ Tiene trabajador asociado: {u.trabajador.nombre}")
    else:
        print(f"   ✗ NO tiene trabajador asociado")

print("\n" + "=" * 60)
