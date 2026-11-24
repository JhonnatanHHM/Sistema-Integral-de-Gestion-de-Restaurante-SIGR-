from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.comun.almacenamiento import AlmacenEnBaseDeDatos
from apps.comun.models import ArchivoMedia
from apps.menu.models import Plato
from apps.menu.tests.test_imagenes import imagen_bytes, subida
from apps.menu.tests.test_vistas import DatosMenuMixin

ALMACEN_BD = {
    "default": {"BACKEND": "apps.comun.almacenamiento.AlmacenEnBaseDeDatos"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


class AlmacenEnBaseDeDatosTests(TestCase):
    def setUp(self):
        self.almacen = AlmacenEnBaseDeDatos()

    def test_guarda_lee_y_borra(self):
        nombre = self.almacen.save("platos/prueba.png", ContentFile(b"contenido"))
        self.assertEqual(nombre, "platos/prueba.png")
        self.assertTrue(self.almacen.exists(nombre))
        self.assertEqual(self.almacen.size(nombre), len(b"contenido"))
        self.assertEqual(self.almacen.open(nombre).read(), b"contenido")
        self.almacen.delete(nombre)
        self.assertFalse(self.almacen.exists(nombre))
        self.almacen.delete(nombre)                       # borrar lo que ya no existe no falla

    def test_un_nombre_repetido_no_pisa_el_archivo_existente(self):
        primero = self.almacen.save("platos/a.png", ContentFile(b"uno"))
        segundo = self.almacen.save("platos/a.png", ContentFile(b"dos"))
        self.assertNotEqual(primero, segundo)
        self.assertEqual(self.almacen.open(primero).read(), b"uno")
        self.assertEqual(self.almacen.open(segundo).read(), b"dos")

    def test_guarda_el_tipo_segun_la_extension_y_arma_la_url(self):
        nombre = self.almacen.save("platos/x.jpg", ContentFile(b"x"))
        self.assertEqual(ArchivoMedia.objects.get(nombre=nombre).tipo, "image/jpeg")
        self.assertEqual(self.almacen.url("platos/x y.jpg"), "/media/platos/x%20y.jpg")


class ServirMediaTests(TestCase):
    def test_entrega_el_archivo_con_su_tipo_y_cache(self):
        ArchivoMedia.objects.create(nombre="platos/f.png", contenido=imagen_bytes(), tipo="image/png")
        respuesta = self.client.get("/media/platos/f.png")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "image/png")
        self.assertIn("max-age", respuesta["Cache-Control"])
        self.assertEqual(respuesta.content, imagen_bytes())

    def test_un_archivo_inexistente_responde_404(self):
        self.assertEqual(self.client.get("/media/platos/no-existe.png").status_code, 404)

    def test_el_nombre_no_se_usa_como_ruta_de_disco(self):
        for nombre in ("../config/settings.py", "..%2F..%2F.env", "platos/../../manage.py", "' OR '1'='1"):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(f"/media/{nombre}").status_code, 404)

    def test_solo_permite_lectura(self):
        ArchivoMedia.objects.create(nombre="platos/f.png", contenido=b"x", tipo="image/png")
        self.assertEqual(self.client.post("/media/platos/f.png").status_code, 405)
        self.assertEqual(self.client.head("/media/platos/f.png").status_code, 200)

    def test_es_publico(self):
        ArchivoMedia.objects.create(nombre="platos/f.png", contenido=b"x", tipo="image/png")
        self.assertEqual(self.client.get("/media/platos/f.png").status_code, 200)       # sin iniciar sesión


@override_settings(STORAGES=ALMACEN_BD)
class FotoPorElFormularioTests(DatosMenuMixin, TestCase):
    """El caso que fallaba en producción: subir la foto con el formulario y poder verla en la carta."""

    def test_la_foto_subida_por_el_formulario_se_ve_en_la_carta_publica(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("menu:plato_nuevo"), {
            "categoria": self.fuertes.pk, "nombre": "Lasaña", "descripcion": "", "precio": "26000",
            "disponible": "on", "destacado": "on", "imagen": subida(),
        })
        self.assertRedirects(respuesta, reverse("menu:plato_lista"))
        plato = Plato.objects.get(nombre="Lasaña")
        self.assertEqual(ArchivoMedia.objects.count(), 1)

        self.client.logout()
        carta = self.client.get(reverse("menu:publico")).content.decode()
        self.assertIn(f'src="{plato.imagen.url}"', carta)
        foto = self.client.get(plato.imagen.url)
        self.assertEqual(foto.status_code, 200)
        self.assertEqual(foto["Content-Type"], "image/png")
        self.assertEqual(foto.content, imagen_bytes())

    def test_reemplazar_o_eliminar_el_plato_borra_la_foto_anterior(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("menu:plato_nuevo"), {
            "categoria": self.fuertes.pk, "nombre": "Lasaña", "descripcion": "", "precio": "26000",
            "disponible": "on", "imagen": subida(),
        })
        plato = Plato.objects.get(nombre="Lasaña")
        primera = plato.imagen.name
        self.client.post(reverse("menu:plato_editar", args=(plato.pk,)), {
            "categoria": self.fuertes.pk, "nombre": "Lasaña", "descripcion": "", "precio": "26000",
            "disponible": "on", "imagen": subida("otra.png"),
        })
        self.assertFalse(ArchivoMedia.objects.filter(nombre=primera).exists())
        self.assertEqual(ArchivoMedia.objects.count(), 1)
        self.client.post(reverse("menu:plato_eliminar", args=(plato.pk,)))
        self.assertEqual(ArchivoMedia.objects.count(), 0)
