import shutil
import tempfile
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from panelfinanzas.models import Producto

from .models import Cliente, ImagenTarea, ProductoTarea, TareaPlanificada


class ImagenesProductoTareaTests(TestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.media_root = tempfile.mkdtemp()
		cls.override_media = override_settings(MEDIA_ROOT=cls.media_root)
		cls.override_media.enable()

	@classmethod
	def tearDownClass(cls):
		cls.override_media.disable()
		shutil.rmtree(cls.media_root, ignore_errors=True)
		super().tearDownClass()

	def setUp(self):
		user_model = get_user_model()
		self.usuario = user_model.objects.create_user(
			username='tester',
			password='secret123',
		)
		self.client.force_login(self.usuario)
		self.producto_catalogo = Producto.objects.create(
			nombre='Filtro premium',
			precio_costo=50000,
			precio_venta=80000,
			creado_por=self.usuario,
		)

	def crear_imagen(self, nombre='foto.png', color='blue'):
		salida = BytesIO()
		imagen = Image.new('RGB', (40, 40), color=color)
		imagen.save(salida, format='PNG')
		salida.seek(0)
		return SimpleUploadedFile(nombre, salida.getvalue(), content_type='image/png')

	def datos_base_tarea(self):
		return {
			'nombre_cliente': 'Cliente Demo',
			'telefono_cliente': '3001234567',
			'placa': '',
			'descripcion_trabajo': 'Cambio de filtro y revisión general',
			'fecha_ingreso': '2026-04-15',
			'fecha_entrega': '2026-04-20',
			'estado': 'pendiente',
			'prioridad': 'media',
			'observaciones': '',
			'monto_abonado': '0',
			'productos-TOTAL_FORMS': '1',
			'productos-INITIAL_FORMS': '0',
			'productos-MIN_NUM_FORMS': '0',
			'productos-MAX_NUM_FORMS': '1000',
			'productos-0-id': '',
			'productos-0-producto': str(self.producto_catalogo.pk),
			'productos-0-nombre_producto_input': self.producto_catalogo.nombre,
			'productos-0-placa': 'ABC123',
			'productos-0-cantidad': '2',
			'productos-0-precio_cobrado': '95000',
		}

	def test_crear_tarea_guarda_imagenes_en_producto(self):
		respuesta = self.client.post(
			reverse('tareas:crear'),
			{
				**self.datos_base_tarea(),
				'productos-0-imagenes': [
					self.crear_imagen('producto-1.png', 'red'),
					self.crear_imagen('producto-2.png', 'green'),
				],
			},
		)

		self.assertEqual(respuesta.status_code, 302)
		self.assertEqual(respuesta.url, reverse('tareas:lista'))
		tarea = TareaPlanificada.objects.get()
		producto_tarea = ProductoTarea.objects.get(tarea=tarea)
		imagenes = ImagenTarea.objects.filter(producto_tarea=producto_tarea)

		self.assertEqual(imagenes.count(), 2)
		self.assertTrue(all(imagen.tarea_id == tarea.id for imagen in imagenes))
		self.assertEqual(tarea.placa, 'ABC123')

	def test_detalle_tarea_sube_imagen_a_producto_especifico(self):
		tarea = TareaPlanificada.objects.create(
			nombre_cliente='Cliente Demo',
			telefono_cliente='3001234567',
			placa='XYZ987',
			descripcion_trabajo='Trabajo existente',
			fecha_ingreso=date(2026, 4, 15),
			fecha_entrega=date(2026, 4, 20),
			estado='pendiente',
			prioridad='media',
		)
		producto_tarea = ProductoTarea.objects.create(
			tarea=tarea,
			producto=self.producto_catalogo,
			nombre_producto=self.producto_catalogo.nombre,
			placa='XYZ987',
			cantidad=1,
			precio_costo=self.producto_catalogo.precio_costo,
			precio_venta=self.producto_catalogo.precio_venta,
			ajuste_precio=0,
		)

		respuesta = self.client.post(
			reverse('tareas:detalle', args=[tarea.pk]),
			{
				'producto_tarea': str(producto_tarea.pk),
				'descripcion': 'Antes de entregar',
				'imagen': self.crear_imagen('detalle.png', 'yellow'),
			},
		)

		self.assertRedirects(respuesta, reverse('tareas:detalle', args=[tarea.pk]))
		imagen = ImagenTarea.objects.get(producto_tarea=producto_tarea)

		self.assertEqual(imagen.tarea_id, tarea.id)
		self.assertEqual(imagen.descripcion, 'Antes de entregar')


class ClientesHistorialTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.usuario = user_model.objects.create_user(
			username='cliente_tester',
			password='secret123',
		)
		self.client.force_login(self.usuario)
		self.cliente = Cliente.objects.create(
			nombre='Cliente Historial',
			telefono='3009998888',
			email='cliente@example.com',
		)
		self.producto = Producto.objects.create(
			nombre='Tapete premium',
			precio_costo=40000,
			precio_venta=70000,
			creado_por=self.usuario,
		)

	def crear_tarea_con_producto(self, fecha_ingreso, monto_abonado):
		tarea = TareaPlanificada.objects.create(
			nombre_cliente=self.cliente.nombre,
			telefono_cliente=self.cliente.telefono,
			placa='TES123',
			descripcion_trabajo='Instalación de tapete',
			fecha_ingreso=fecha_ingreso,
			fecha_entrega=fecha_ingreso,
			estado='completado',
			prioridad='media',
			monto_abonado=monto_abonado,
		)
		ProductoTarea.objects.create(
			tarea=tarea,
			producto=self.producto,
			nombre_producto=self.producto.nombre,
			placa='TES123',
			cantidad=1,
			precio_costo=self.producto.precio_costo,
			precio_venta=self.producto.precio_venta,
			ajuste_precio=0,
		)
		return tarea

	def test_lista_clientes_incluye_historial_y_deuda(self):
		self.crear_tarea_con_producto(date(2026, 4, 10), 30000)
		self.crear_tarea_con_producto(date(2026, 4, 12), 70000)

		respuesta = self.client.get(reverse('tareas:lista_clientes'))

		self.assertEqual(respuesta.status_code, 200)
		self.assertContains(respuesta, f'modalCliente{self.cliente.pk}')
		self.assertContains(respuesta, 'Historial de compras')
		cliente = next(c for c in respuesta.context['clientes'] if c.pk == self.cliente.pk)
		self.assertEqual(cliente.total_compras, 2)
		self.assertTrue(cliente.debe)
		self.assertEqual(cliente.saldo_pendiente_total, Decimal('40000'))
