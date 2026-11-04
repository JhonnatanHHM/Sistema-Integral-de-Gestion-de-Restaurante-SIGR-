from django.test import TestCase
from django.urls import reverse


class InicioTests(TestCase):
    def test_inicio_responde_200(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "SIGR")
