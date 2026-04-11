from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Trabajador
import secrets
import string
import unicodedata
import re


def _generar_username(nombre):
    """Genera un username sanitizado basado en el nombre"""
    # Normalizar acentos
    nombre_normalizado = unicodedata.normalize('NFKD', nombre)
    nombre_sin_acentos = ''.join([c for c in nombre_normalizado if not unicodedata.combining(c)])
    
    # Convertir a minúsculas y reemplazar espacios con guiones
    username = nombre_sin_acentos.lower().replace(' ', '_')
    
    # Remover caracteres no alfanuméricos (excepto guiones bajos)
    username = re.sub(r'[^a-z0-9_]', '', username)
    
    # Limitar a 150 caracteres (límite de Django)
    username = username[:150]
    
    return username


def _generar_contraseña(longitud=12):
    """Genera una contraseña aleatoria segura"""
    caracteres = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))


@receiver(post_save, sender=Trabajador)
def crear_usuario_trabajador(sender, instance, created, **kwargs):
    """
    Señal para crear automáticamente un usuario cuando se crea un nuevo Trabajador.
    Solo crea usuario si el trabajador no tiene uno asignado aún.
    """
    if created and instance.usuario is None:
        try:
            # Generar username único
            base_username = _generar_username(instance.nombre)
            username = base_username
            contador = 1
            
            # Si el username ya existe, agregar número
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{contador}"
                contador += 1
            
            # Generar contraseña
            contraseña = _generar_contraseña()
            
            # Crear usuario
            usuario = User.objects.create_user(
                username=username,
                password=contraseña,
                first_name=instance.nombre.split()[0] if instance.nombre else 'Trabajador',
                last_name=' '.join(instance.nombre.split()[1:]) if len(instance.nombre.split()) > 1 else '',
            )
            
            # Asignar a grupo 'trabajador'
            try:
                grupo = Group.objects.get(name='trabajador')
                usuario.groups.add(grupo)
            except Group.DoesNotExist:
                # Si el grupo no existe, crearlo
                grupo = Group.objects.create(name='trabajador')
                usuario.groups.add(grupo)
            
            # Asociar usuario al trabajador
            instance.usuario = usuario
            instance.save(update_fields=['usuario'])
            
        except Exception as e:
            print(f"Error creando usuario para {instance.nombre}: {str(e)}")
