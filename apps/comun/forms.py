import re
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError


class MontoField(forms.DecimalField):
    """Campo de dinero: solo dígitos, con hasta 2 decimales (punto o coma), positivo y de máximo 9 dígitos."""

    patron = re.compile(r"^\d{1,7}([.,]\d{1,2})?$")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_digits", 9)
        kwargs.setdefault("decimal_places", 2)
        kwargs.setdefault("min_value", Decimal("0.01"))
        super().__init__(*args, **kwargs)
        self.widget.attrs.update({"inputmode": "decimal"})

    def to_python(self, value):
        if value in self.empty_values:
            return None
        texto = str(value).strip()
        if not self.patron.match(texto):
            raise ValidationError(
                "Ingresa un valor numérico positivo con hasta 2 decimales (ej. 12500 o 12500.50).", code="invalid"
            )
        return super().to_python(texto.replace(",", "."))
