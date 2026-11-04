"""Validadores y normalizadores compartidos por todos los módulos."""
from django.core.validators import RegexValidator


# Rango de mesas del restaurante (lo comparten pedidos y reservas)
MESA_MIN = 1
MESA_MAX = 99


def limpiar_espacios(valor):
    """Quita espacios al inicio y al final y colapsa los espacios (y saltos de línea) repetidos."""
    return " ".join((valor or "").split())


validar_nombre_comercial = RegexValidator(
    regex=r"^\w[\w ,.'&()/\-]*$",
    message="Usa solo letras, números, espacios y los signos , . ' & ( ) / -",
    code="nombre_invalido",
)

validar_texto_libre = RegexValidator(
    regex=r"^[^<>\x00-\x08\x0b-\x1f\x7f]*$",
    message="El texto contiene caracteres no permitidos (< >, o de control).",
    code="texto_invalido",
)
