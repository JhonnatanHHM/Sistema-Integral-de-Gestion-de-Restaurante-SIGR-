from django import forms

from apps.comun.validators import MESA_MAX, MESA_MIN, limpiar_espacios, validar_texto_libre
from apps.menu.models import Plato

from .models import MAX_CANTIDAD, Estado


class PedidoForm(forms.Form):
    """Pedido: mesa, notas y una cantidad por cada plato disponible.

    Los campos de cantidad se generan solo para platos disponibles; cualquier otro dato enviado se ignora,
    y los precios nunca se reciben del navegador.
    """

    mesa = forms.IntegerField(
        label="Mesa", min_value=MESA_MIN, max_value=MESA_MAX,
        widget=forms.NumberInput(attrs={"min": MESA_MIN, "max": MESA_MAX, "inputmode": "numeric"}),
    )
    notas = forms.CharField(
        label="Notas para la cocina", required=False, max_length=200, validators=[validar_texto_libre],
        widget=forms.Textarea(attrs={"rows": 2, "maxlength": 200}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platos = list(
            Plato.objects.filter(disponible=True, categoria__activa=True).select_related("categoria")
        )
        for plato in self.platos:
            self.fields[f"plato_{plato.pk}"] = forms.IntegerField(
                label=plato.nombre, required=False, min_value=0, max_value=MAX_CANTIDAD, initial=0,
                widget=forms.NumberInput(attrs={"min": 0, "max": MAX_CANTIDAD, "inputmode": "numeric"}),
            )
        self.items = []

    def clean_notas(self):
        return limpiar_espacios(self.cleaned_data.get("notas", ""))

    def clean(self):
        datos = super().clean()
        self.items = [
            (plato, datos[f"plato_{plato.pk}"])
            for plato in self.platos
            if datos.get(f"plato_{plato.pk}")
        ]
        if not self.errors and not self.items:
            raise forms.ValidationError("Agrega al menos un plato al pedido.")
        return datos

    def grupos(self):
        """Campos de cantidad agrupados por categoría, para dibujarlos en la plantilla."""
        grupos = []
        for plato in self.platos:
            if not grupos or grupos[-1][0] != plato.categoria:
                grupos.append((plato.categoria, []))
            grupos[-1][1].append((plato, self[f"plato_{plato.pk}"]))
        return grupos


class FiltroPedidoForm(forms.Form):
    estado = forms.ChoiceField(
        label="Estado", required=False,
        choices=[("", "Todos"), ("activos", "Activos")] + list(Estado.choices),
    )
    mesa = forms.IntegerField(
        label="Mesa", required=False, min_value=MESA_MIN, max_value=MESA_MAX,
        widget=forms.NumberInput(attrs={"min": MESA_MIN, "max": MESA_MAX}),
    )


class CambioEstadoForm(forms.Form):
    """Estado que el usuario veía al pulsar el botón: evita saltarse pasos si otro ya avanzó el pedido."""

    desde = forms.ChoiceField(choices=Estado.choices)
