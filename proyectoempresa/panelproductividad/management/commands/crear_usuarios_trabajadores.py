from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from panelproductividad.models import Trabajador
import secrets
import string


class Command(BaseCommand):
    help = 'Crea usuarios de Django para todos los trabajadores sin usuario asignado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña personalizada (si no se proporciona, se genera una aleatoria)',
        )
        parser.add_argument(
            '--crear-grupo',
            action='store_true',
            help='Crea el grupo "trabajador" si no existe',
        )

    def handle(self, *args, **options):
        # Crear grupo "trabajador" si no existe
        if options['crear_grupo']:
            grupo, creado = Group.objects.get_or_create(name='trabajador')
            if creado:
                self.stdout.write(self.style.SUCCESS('✓ Grupo "trabajador" creado'))
            else:
                self.stdout.write('✓ Grupo "trabajador" ya existe')

        # Obtener el grupo "trabajador"
        try:
            grupo_trabajador = Group.objects.get(name='trabajador')
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Advertencia: El grupo "trabajador" no existe. Cree con --crear-grupo'))
            grupo_trabajador = None

        # Obtener trabajadores sin usuario
        trabajadores_sin_usuario = Trabajador.objects.filter(usuario__isnull=True)
        
        if not trabajadores_sin_usuario.exists():
            self.stdout.write(self.style.WARNING('⚠ No hay trabajadores sin usuario asignado'))
            return

        self.stdout.write(f'\n📋 Creando usuarios para {trabajadores_sin_usuario.count()} trabajadores...\n')

        contraseña_personalizada = options.get('password')
        usuarios_creados = []

        for trabajador in trabajadores_sin_usuario:
            # Generar username basado en el nombre
            username_base = trabajador.nombre.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            username = username_base
            contador = 1

            # Asegurar que el username sea único
            while User.objects.filter(username=username).exists():
                username = f"{username_base}_{contador}"
                contador += 1

            # Usar contraseña personalizada o generar una aleatoria
            if contraseña_personalizada:
                password = contraseña_personalizada
            else:
                password = self._generar_contraseña()

            # Crear usuario
            usuario = User.objects.create_user(
                username=username,
                email=f"{username}@empresa.local",
                password=password,
                first_name=trabajador.nombre.split()[0],
                last_name=' '.join(trabajador.nombre.split()[1:]) if len(trabajador.nombre.split()) > 1 else '',
            )

            # Asignar al grupo "trabajador"
            if grupo_trabajador:
                usuario.groups.add(grupo_trabajador)
                usuario.save()

            # Vincular usuario con trabajador
            trabajador.usuario = usuario
            trabajador.save()

            usuarios_creados.append({
                'trabajador': trabajador.nombre,
                'usuario': username,
                'contraseña': password,
            })

            self.stdout.write(
                self.style.SUCCESS(f'✓ {trabajador.nombre}')
            )

        # Mostrar resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\n✅ {len(usuarios_creados)} usuarios creados exitosamente\n'))
        
        self.stdout.write('📝 Resumen de Credenciales:\n')
        self.stdout.write('-' * 60)
        
        for info in usuarios_creados:
            self.stdout.write(f"\n👤 Trabajador: {info['trabajador']}")
            self.stdout.write(f"   Usuario: {info['usuario']}")
            self.stdout.write(f"   Contraseña: {info['contraseña']}")
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.WARNING(
            '\n⚠️  IMPORTANTE: Guarden estas credenciales en un lugar seguro.'
        ))
        self.stdout.write('Los usuarios pueden cambiar su contraseña después de iniciar sesión.\n')

    def _generar_contraseña(self, longitud=12):
        """Genera una contraseña aleatoria segura"""
        caracteres = string.ascii_letters + string.digits + string.punctuation.replace('"', '').replace("'", '')
        return ''.join(secrets.choice(caracteres) for _ in range(longitud))
