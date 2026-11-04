import os
import shutil
import tempfile
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.comun.validators import validar_imagen
from apps.menu.forms import PlatoForm
from apps.menu.models import Categoria, Plato

from .test_vistas import DatosMenuMixin


def imagen_bytes(formato="PNG", tamano=(40, 30)):
    buffer = BytesIO()
    Image.new("RGB", tamano, (200, 120, 50)).save(buffer, format=formato)
    return buffer.getvalue()


def subida(nombre="plato.png", contenido=None, tipo="image/png"):
    return SimpleUploadedFile(nombre, imagen_bytes() if contenido is None else contenido, content_type=tipo)


class MediaTemporalMixin:
    """Las fotos de las pruebas se guardan en una carpeta temporal que se borra al terminar."""

    def setUp(self):
        super().setUp()
        self.media = tempfile.mkdtemp(prefix="media_prueba_")
        configuracion = override_settings(MEDIA_ROOT=self.media)
        configuracion.enable()
        self.addCleanup(configuracion.disable)
        self.addCleanup(shutil.rmtree, self.media, True)

    def archivos_guardados(self):
        carpeta = os.path.join(self.media, "platos")
        return sorted(os.listdir(carpeta)) if os.path.isdir(carpeta) else []


class ValidarImagenTests(TestCase):
    def test_acepta_jpg_png_y_webp_reales(self):
        for formato, nombre in (("PNG", "a.png"), ("JPEG", "a.jpg"), ("JPEG", "a.jpeg"), ("WEBP", "a.webp")):
            with self.subTest(formato=formato, nombre=nombre):
                validar_imagen(subida(nombre, imagen_bytes(formato)))

    def test_rechaza_extensiones_no_permitidas(self):
        for nombre in ("a.svg", "a.gif", "a.bmp", "a.php", "a.html", "a.exe", "sin_extension", "a.png.exe", "a.PNG.svg"):
            with self.subTest(nombre=nombre):
                with self.assertRaises(ValidationError):
                    validar_imagen(subida(nombre, imagen_bytes()))

    def test_rechaza_archivos_que_no_son_imagenes_aunque_tengan_extension_de_imagen(self):
        falsos = {
            "texto.png": b"esto no es una imagen",
            "script.jpg": b"<script>alert(1)</script>",
            "svg.png": b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            "php.png": b"<?php system($_GET['c']); ?>",
            "vacio.png": b"",
            "truncada.png": imagen_bytes()[:30],
        }
        for nombre, contenido in falsos.items():
            with self.subTest(nombre=nombre):
                with self.assertRaises(ValidationError):
                    validar_imagen(subida(nombre, contenido))

    def test_el_contenido_debe_coincidir_con_la_extension(self):
        for nombre, formato in (("a.jpg", "PNG"), ("a.png", "JPEG"), ("a.png", "GIF"), ("a.webp", "PNG")):
            with self.subTest(nombre=nombre, formato=formato):
                with self.assertRaises(ValidationError):
                    validar_imagen(subida(nombre, imagen_bytes(formato)))

    def test_limite_de_peso(self):
        with self.assertRaises(ValidationError) as error:
            validar_imagen(subida("a.png", b"x" * (2 * 1024 * 1024 + 1)))
        self.assertIn("2 MB", str(error.exception))

    def test_limite_de_dimensiones(self):
        validar_imagen(subida("a.png", imagen_bytes(tamano=(4000, 10))))
        with self.assertRaises(ValidationError):
            validar_imagen(subida("a.png", imagen_bytes(tamano=(4001, 10))))
        with self.assertRaises(ValidationError):
            validar_imagen(subida("a.png", imagen_bytes(tamano=(10, 4001))))


class FotoDelPlatoModeloTests(MediaTemporalMixin, DatosMenuMixin, TestCase):
    def test_se_guarda_con_nombre_aleatorio_y_no_con_el_del_navegador(self):
        self.pasta.imagen = subida("../../etc/foto original.png")
        self.pasta.save()
        self.assertRegex(self.pasta.imagen.name, r"^platos/[0-9a-f]{32}\.png$")
        self.assertNotIn("etc", self.pasta.imagen.name)
        self.assertEqual(len(self.archivos_guardados()), 1)

    def test_doble_extension_solo_conserva_la_ultima(self):
        self.pasta.imagen = subida("foto.php.png")
        self.pasta.save()
        self.assertRegex(self.pasta.imagen.name, r"\.png$")
        self.assertNotIn("php", self.pasta.imagen.name)

    def test_al_reemplazar_la_foto_se_borra_la_anterior(self):
        self.pasta.imagen = subida()
        self.pasta.save()
        primera = self.pasta.imagen.name
        self.pasta.imagen = subida("otra.png")
        self.pasta.save()
        self.assertNotEqual(self.pasta.imagen.name, primera)
        self.assertEqual(len(self.archivos_guardados()), 1)

    def test_al_quitar_la_foto_se_borra_el_archivo(self):
        self.pasta.imagen = subida()
        self.pasta.save()
        self.pasta.imagen = ""
        self.pasta.save()
        self.assertEqual(self.archivos_guardados(), [])

    def test_al_eliminar_el_plato_se_borra_su_foto(self):
        self.pasta.imagen = subida()
        self.pasta.save()
        self.pasta.delete()
        self.assertEqual(self.archivos_guardados(), [])

    def test_guardar_sin_cambiar_la_foto_no_la_borra(self):
        self.pasta.imagen = subida()
        self.pasta.save()
        self.pasta.refresh_from_db()
        self.pasta.precio = 30000
        self.pasta.save()
        self.assertEqual(len(self.archivos_guardados()), 1)


class FotoDelPlatoFormularioTests(MediaTemporalMixin, DatosMenuMixin, TestCase):
    def datos(self, **cambios):
        base = {"categoria": self.fuertes.pk, "nombre": "Lasaña", "descripcion": "De la casa", "precio": "26000", "disponible": "on"}
        base.update(cambios)
        return base

    def test_el_formulario_rechaza_archivos_falsos(self):
        form = PlatoForm(self.datos(), {"imagen": subida("falsa.png", b"<script>alert(1)</script>")})
        self.assertFalse(form.is_valid())
        self.assertIn("imagen", form.errors)

    def test_la_foto_es_opcional(self):
        self.assertTrue(PlatoForm(self.datos()).is_valid())

    def test_editar_sin_subir_foto_conserva_la_existente(self):
        self.pasta.imagen = subida()
        self.pasta.save()
        form = PlatoForm(
            {"categoria": self.fuertes.pk, "nombre": "Pasta alfredo", "descripcion": "", "precio": "28000", "disponible": "on"},
            instance=self.pasta,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(len(self.archivos_guardados()), 1)


class FotoDelPlatoVistasTests(MediaTemporalMixin, DatosMenuMixin, TestCase):
    def test_el_administrador_crea_un_plato_con_foto_y_lo_marca_destacado(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("menu:plato_nuevo"), {
            "categoria": self.fuertes.pk, "nombre": "Lasaña", "descripcion": "", "precio": "26000",
            "disponible": "on", "destacado": "on", "imagen": subida(),
        })
        self.assertRedirects(respuesta, reverse("menu:plato_lista"))
        plato = Plato.objects.get(nombre="Lasaña")
        self.assertTrue(plato.destacado)
        self.assertRegex(plato.imagen.name, r"^platos/[0-9a-f]{32}\.png$")
        self.assertEqual(len(self.archivos_guardados()), 1)

    def test_un_archivo_falso_no_crea_el_plato_ni_deja_archivos(self):
        self.client.force_login(self.admin)
        for nombre, contenido in (("x.png", b"no soy imagen"), ("x.svg", b"<svg></svg>"), ("x.php", b"<?php ?>")):
            respuesta = self.client.post(reverse("menu:plato_nuevo"), {
                "categoria": self.fuertes.pk, "nombre": "Lasaña", "descripcion": "", "precio": "26000",
                "imagen": subida(nombre, contenido),
            })
            self.assertEqual(respuesta.status_code, 200, nombre)
        self.assertFalse(Plato.objects.filter(nombre="Lasaña").exists())
        self.assertEqual(self.archivos_guardados(), [])

    def test_el_mesero_no_puede_subir_fotos(self):
        self.client.force_login(self.mesero)
        respuesta = self.client.post(reverse("menu:plato_editar", args=[self.pasta.pk]), {
            "categoria": self.fuertes.pk, "nombre": "Pasta alfredo", "precio": "28000", "imagen": subida(),
        })
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(self.archivos_guardados(), [])

    def test_la_carta_publica_muestra_la_foto_solo_de_los_platos_que_la_tienen(self):
        self.pasta.imagen = subida()
        self.pasta.save()
        pagina = self.client.get(reverse("menu:publico")).content.decode()
        self.assertEqual(pagina.count('class="plato__miniatura"'), 1)
        self.assertIn(self.pasta.imagen.url, pagina)
