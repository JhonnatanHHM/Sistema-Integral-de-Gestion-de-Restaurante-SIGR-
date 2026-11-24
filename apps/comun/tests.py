from unittest.mock import patch

from django.db import OperationalError
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class SaludTests(TestCase):
    def test_responde_ok_sin_sesion(self):
        respuesta = self.client.get(reverse("salud"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"estado": "ok", "base_de_datos": "ok"})

    def test_es_json_y_solo_lectura(self):
        self.assertEqual(self.client.get(reverse("salud"))["Content-Type"], "application/json")
        self.assertEqual(self.client.head(reverse("salud")).status_code, 200)
        for metodo in ("post", "put", "delete"):
            self.assertEqual(getattr(self.client, metodo)(reverse("salud")).status_code, 405)

    def test_responde_503_si_la_base_de_datos_falla(self):
        with patch("apps.comun.views.connection.cursor", side_effect=OperationalError("sin conexion")):
            respuesta = self.client.get(reverse("salud"))
        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(respuesta.json()["estado"], "error")
        self.assertNotIn("sin conexion", respuesta.content.decode())     # no filtra detalles internos

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r"^salud/$"])
    def test_no_se_redirige_a_https(self):
        cliente = Client()
        self.assertEqual(cliente.get(reverse("salud")).status_code, 200)
        self.assertEqual(cliente.get("/").status_code, 301)
