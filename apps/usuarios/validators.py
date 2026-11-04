"""Validadores y normalizadores reutilizables para los datos de personas."""
import re

from django.core.validators import RegexValidator

validar_nombre = RegexValidator(
    regex=r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$",
    message="Solo se permiten letras, espacios, guion o apóstrofo.",
    code="nombre_invalido",
)

validar_telefono = RegexValidator(
    regex=r"^\+?\d{7,15}$",
    message="Ingresa un teléfono válido: de 7 a 15 dígitos, con + opcional al inicio.",
    code="telefono_invalido",
)


def limpiar_espacios(valor):
    """Quita espacios al inicio y al final y colapsa los espacios repetidos."""
    return " ".join((valor or "").split())


def normalizar_telefono(valor):
    """Elimina espacios, guiones y paréntesis, dejando solo dígitos y un + inicial."""
    return re.sub(r"[\s\-().]", "", valor or "")
