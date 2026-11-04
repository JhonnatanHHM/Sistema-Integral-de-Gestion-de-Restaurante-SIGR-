import re
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError


class MontoField(forms.DecimalField):
    """Campo de dinero: solo dígitos, con hasta `decimal_places` decimales (punto o coma) y de `max_digits` como máximo.

    Por defecto: positivo, 2 decimales y 9 dígitos en total. Rechaza notación científica, signos, símbolos y NaN.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_digits", 9)
        kwargs.setdefault("decimal_places", 2)
        kwargs.setdefault("min_value", Decimal("0.01"))
        super().__init__(*args, **kwargs)
        enteros = self.max_digits - self.decimal_places
        self.patron = re.compile(rf"^\d{{1,{enteros}}}([.,]\d{{1,{self.decimal_places}}})?$")
        self.widget.attrs.update({"inputmode": "decimal"})

    def to_python(self, value):
        if value in self.empty_values:
            return None
        texto = str(value).strip()
        if not self.patron.match(texto):
            raise ValidationError(
                "Ingresa un valor numérico sin signos ni símbolos, con hasta "
                f"{self.decimal_places} decimales (ej. 12500 o 12500.50).",
                code="invalid",
            )
        return super().to_python(texto.replace(",", "."))
