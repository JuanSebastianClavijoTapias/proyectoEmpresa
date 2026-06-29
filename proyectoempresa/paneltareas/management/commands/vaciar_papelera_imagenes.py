from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from paneltareas.models import ImagenTarea


class Command(BaseCommand):
    help = 'Elimina definitivamente las imágenes que llevan más de 30 días en la papelera'

    def handle(self, *args, **options):
        corte = timezone.now() - timedelta(days=30)
        imagenes = ImagenTarea.objects.papelera().filter(eliminada_en__lt=corte)
        total = imagenes.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay imágenes para vaciar de la papelera.'))
            return

        eliminadas = 0
        for img in imagenes:
            try:
                if img.imagen:
                    img.imagen.delete(save=False)
                img.delete()
                eliminadas += 1
            except Exception as e:
                self.stderr.write(f'Error eliminando imagen {img.pk}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'Vaciado de papelera completado: {eliminadas} de {total} imagen(es) eliminadas definitivamente.'
        ))
