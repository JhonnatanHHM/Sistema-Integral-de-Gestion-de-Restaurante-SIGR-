import os
from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.usuarios.models import Rol, Usuario

CLAVE = "Clave-Segura-2026!"


def ejecutar(**entorno):
    """Corre el comando con exactamente las variables indicadas y devuelve su salida."""
    salida = StringIO()
    with patch.dict(os.environ, entorno, clear=False):
        call_command("crear_admin_inicial", stdout=salida)
    return salida.getvalue()


class CrearAdminInicialTests(TestCase):
    def setUp(self):
        for variable in ("SIGR_ADMIN_EMAIL", "SIGR_ADMIN_PASSWORD", "SIGR_ADMIN_NOMBRE", "SIGR_ADMIN_APELLIDO"):
            os.environ.pop(variable, None)

    def test_crea_el_administrador(self):
        ejecutar(SIGR_ADMIN_EMAIL="Jefe@Restaurante.test", SIGR_ADMIN_PASSWORD=CLAVE)
        admin = Usuario.objects.get(email="jefe@restaurante.test")
        self.assertEqual(admin.rol, Rol.ADMINISTRADOR)
        self.assertTrue(admin.is_staff and admin.is_superuser)
        self.assertTrue(admin.check_password(CLAVE))

    def test_usa_nombre_y_apellido_indicados(self):
        ejecutar(SIGR_ADMIN_EMAIL="a@b.test", SIGR_ADMIN_PASSWORD=CLAVE, SIGR_ADMIN_NOMBRE="Jhonnatan", SIGR_ADMIN_APELLIDO="Henao")
        self.assertEqual(Usuario.objects.get().nombre_completo, "Jhonnatan Henao")

    def test_es_idempotente_y_no_pisa_la_contrasena(self):
        ejecutar(SIGR_ADMIN_EMAIL="a@b.test", SIGR_ADMIN_PASSWORD=CLAVE)
        salida = ejecutar(SIGR_ADMIN_EMAIL="a@b.test", SIGR_ADMIN_PASSWORD="Otra-Clave-Distinta-9!")
        self.assertIn("no se modifica", salida)
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertTrue(Usuario.objects.get().check_password(CLAVE))

    def test_no_convierte_en_administrador_una_cuenta_existente(self):
        Usuario.objects.create_user("cliente@b.test", CLAVE, first_name="Ana", last_name="Gil")
        ejecutar(SIGR_ADMIN_EMAIL="cliente@b.test", SIGR_ADMIN_PASSWORD=CLAVE)
        self.assertEqual(Usuario.objects.get().rol, Rol.CLIENTE)

    def test_rechaza_entradas_invalidas(self):
        casos = [
            {},                                                                        # faltan variables
            {"SIGR_ADMIN_EMAIL": "a@b.test"},                                          # falta la contrasena
            {"SIGR_ADMIN_EMAIL": "no-es-un-correo", "SIGR_ADMIN_PASSWORD": CLAVE},
            {"SIGR_ADMIN_EMAIL": "a@b.test", "SIGR_ADMIN_PASSWORD": "12345678"},       # contrasena debil
            {"SIGR_ADMIN_EMAIL": "a@b.test", "SIGR_ADMIN_PASSWORD": CLAVE, "SIGR_ADMIN_NOMBRE": "<script>"},
            {"SIGR_ADMIN_EMAIL": "' OR '1'='1", "SIGR_ADMIN_PASSWORD": CLAVE},
        ]
        for entorno in casos:
            with self.subTest(entorno=entorno), self.assertRaises(CommandError):
                ejecutar(**entorno)
        self.assertFalse(Usuario.objects.exists())
