"""Crea el primer administrador a partir de variables de entorno (idempotente).

Pensado para despliegues sin terminal (por ejemplo, el plan gratuito de Render), donde no se puede ejecutar `createsuperuser`.
Variables: SIGR_ADMIN_EMAIL y SIGR_ADMIN_PASSWORD (obligatorias); SIGR_ADMIN_NOMBRE y SIGR_ADMIN_APELLIDO (opcionales).
Si ya existe una cuenta con ese correo no se modifica nada (no se pisa una contraseña). El resto del personal y los clientes
se crean después desde la propia aplicación. Uso: python manage.py crear_admin_inicial"""
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from apps.usuarios.models import Usuario
from apps.usuarios.validators import validar_nombre


class Command(BaseCommand):
    help = "Crea el administrador inicial desde SIGR_ADMIN_EMAIL y SIGR_ADMIN_PASSWORD si no existe"

    def handle(self, *args, **opciones):
        correo = os.environ.get("SIGR_ADMIN_EMAIL", "").strip().lower()
        contrasena = os.environ.get("SIGR_ADMIN_PASSWORD", "")
        nombre = os.environ.get("SIGR_ADMIN_NOMBRE", "Administrador").strip()
        apellido = os.environ.get("SIGR_ADMIN_APELLIDO", "SIGR").strip()
        if not correo or not contrasena:
            raise CommandError("Define SIGR_ADMIN_EMAIL y SIGR_ADMIN_PASSWORD.")

        if Usuario.objects.filter(email=correo).exists():
            self.stdout.write(f"Ya existe una cuenta con {correo}: no se modifica.")
            return

        try:
            validate_email(correo)
            validar_nombre(nombre)
            validar_nombre(apellido)
            validate_password(contrasena)
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from None

        Usuario.objects.create_superuser(correo, contrasena, first_name=nombre, last_name=apellido)
        self.stdout.write(self.style.SUCCESS(f"Administrador creado: {correo}"))
