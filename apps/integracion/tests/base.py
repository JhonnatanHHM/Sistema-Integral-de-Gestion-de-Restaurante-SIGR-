from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone

from apps.usuarios.models import Rol, Usuario

CLAVE = "Contr4seña-Muy-Segura!"
AHORA = timezone.make_aware(datetime(2026, 11, 10, 10, 0))      # el reloj de las pruebas queda fijo


def crear_usuario(email, rol):
    return Usuario.objects.create_user(email, CLAVE, first_name="Nombre", last_name="Apellido", rol=rol)


class EntornoMixin:
    """Reloj fijo, menú de demostración y un usuario de cada rol."""

    def setUp(self):
        parche = patch("django.utils.timezone.now", return_value=AHORA)
        parche.start()
        self.addCleanup(parche.stop)
        call_command("cargar_menu_demo", stdout=StringIO())
        self.cliente = crear_usuario("cli@ejemplo.com", Rol.CLIENTE)
        self.mesero = crear_usuario("mes@ejemplo.com", Rol.MESERO)
        self.admin = crear_usuario("adm@ejemplo.com", Rol.ADMINISTRADOR)
