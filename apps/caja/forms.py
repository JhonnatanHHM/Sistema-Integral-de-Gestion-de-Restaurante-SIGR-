from datetime import timedelta
from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.comun.forms import MontoField
from apps.comun.validators import limpiar_espacios

from .models import CierreCaja
from .services import pedidos_activos_del_dia

FORMATO_FECHA = "%Y-%m-%d"
DIAS_MAX_REPORTE = 366


def _campo_fecha(etiqueta, **kwargs):
    return forms.DateField(
        label=etiqueta, input_formats=[FORMATO_FECHA],
        widget=forms.DateInput(attrs={"type": "date"}, format=FORMATO_FECHA), **kwargs,
    )


class CierreCajaForm(forms.ModelForm):
    fecha = _campo_fecha("Fecha")
    efectivo_contado = MontoField(label="Efectivo contado", max_digits=12, min_value=Decimal("0"))

    class Meta:
        model = CierreCaja
        fields = ("fecha", "efectivo_contado", "observaciones")
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 2, "maxlength": 200})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].widget.attrs["max"] = timezone.localdate().strftime(FORMATO_FECHA)

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha > timezone.localdate():
            raise forms.ValidationError("No se puede cerrar la caja de una fecha futura.")
        activos = pedidos_activos_del_dia(fecha)
        if activos:
            raise forms.ValidationError(
                f"Aún hay {activos} pedido(s) de ese día sin cerrar o cancelar. Ciérralos antes de cerrar la caja."
            )
        return fecha

    def clean_observaciones(self):
        return limpiar_espacios(self.cleaned_data.get("observaciones", ""))


class RangoFechasForm(forms.Form):
    """Rango del reporte de ventas: formato ISO, desde <= hasta <= hoy y máximo un año."""

    desde = _campo_fecha("Desde")
    hasta = _campo_fecha("Hasta")

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta:
            if desde > hasta:
                self.add_error("desde", "La fecha inicial no puede ser posterior a la final.")
            elif hasta > timezone.localdate():
                self.add_error("hasta", "La fecha final no puede ser futura.")
            elif hasta - desde > timedelta(days=DIAS_MAX_REPORTE):
                self.add_error("desde", f"El rango no puede superar {DIAS_MAX_REPORTE} días.")
        return datos
