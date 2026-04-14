"""
Script para asignar contraseñas a trabajadores sin usuario o sin contraseña
Uso: python manage.py asignar_contraseñas [--generar] [--trabajador_id=X]
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from panelproductividad.models import Trabajador
import secrets
import string


def generar_contraseña(longitud=8):
    """Genera una contraseña aleatoria segura"""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))


class Command(BaseCommand):
    help = 'Asigna contraseñas a trabajadores sin usuario o actualiza sus contraseñas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--generar',
            action='store_true',
            help='Generar contraseñas aleatorias automáticamente',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Aplicar a todos los trabajadores sin contraseña',
        )
        parser.add_argument(
            '--trabajador_id',
            type=int,
            help='ID del trabajador específico',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== ASIGNAR CONTRASEÑAS A TRABAJADORES ===\n'))
        
        # Obtener trabajadores según opción
        if options['trabajador_id']:
            trabajadores = Trabajador.objects.filter(pk=options['trabajador_id'])
        else:
            trabajadores = Trabajador.objects.all()
        
        # Filtrar por estado
        sin_usuario = []
        con_usuario = []
        
        for trab in trabajadores:
            if not trab.usuario:
                sin_usuario.append(trab)
            else:
                con_usuario.append(trab)
        
        # Mostrar estado actual
        self.stdout.write(self.style.WARNING(f'\nTrabajadores sin usuario: {len(sin_usuario)}'))
        for trab in sin_usuario:
            self.stdout.write(f'  - {trab.id}: {trab.nombre}')
        
        self.stdout.write(self.style.WARNING(f'\nTrabajadores con usuario: {len(con_usuario)}'))
        for trab in con_usuario:
            self.stdout.write(f'  - {trab.id}: {trab.nombre} (usuario: {trab.usuario.username})')
        
        if not options['generar'] and not options['all']:
            self.stdout.write(self.style.NOTICE(
                '\nUsa --generar para crear usuarios automáticamente\n'
                'O --all para actualizar todos con contraseñas nuevas\n'
            ))
            return
        
        # Crear usuarios para los sin usuario
        if sin_usuario and options['generar']:
            self.stdout.write(self.style.WARNING(f'\n→ Creando {len(sin_usuario)} usuarios...\n'))
            
            for trab in sin_usuario:
                # Generar username
                from panelproductividad.signals import _generar_username
                username = _generar_username(trab.nombre)
                contador = 1
                while User.objects.filter(username=username).exists():
                    username = f"{_generar_username(trab.nombre)}{contador}"
                    contador += 1
                
                # Generar contraseña
                contraseña = generar_contraseña()
                
                try:
                    usuario = User.objects.create_user(
                        username=username,
                        password=contraseña,
                        first_name=trab.nombre.split()[0] if trab.nombre else 'Trabajador'
                    )
                    trab.usuario = usuario
                    trab.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {trab.nombre}')
                        + f'\n    Usuario: {username}'
                        + f'\n    Contraseña: {contraseña}\n'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error en {trab.nombre}: {str(e)}\n')
                    )
        
        # Actualizador de contraseñas para todos
        if options['all'] and options['generar']:
            self.stdout.write(self.style.WARNING(f'\n→ Actualizando contraseñas de {len(con_usuario)} trabajadores...\n'))
            
            for trab in con_usuario:
                contraseña = generar_contraseña()
                try:
                    trab.usuario.set_password(contraseña)
                    trab.usuario.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {trab.nombre}')
                        + f'\n    Usuario: {trab.usuario.username}'
                        + f'\n    Contraseña nueva: {contraseña}\n'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error en {trab.nombre}: {str(e)}\n')
                    )
        
        self.stdout.write(self.style.SUCCESS('\n✓ Proceso completado\n'))
