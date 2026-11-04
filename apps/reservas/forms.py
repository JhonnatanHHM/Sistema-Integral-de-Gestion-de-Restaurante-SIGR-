from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from apps.comun.validators import MESA_MAX, MESA_MIN, limpiar_espacios

from .models import EstadoReserva, Reserva
from .reglas import ANTICIPACION_MINIMA, DIAS_MAX_ANTICIPACION, PERSONAS_MAX, franjas
from .services import conflictos

FORMATO_FECHA = "%Y-%m-%d"


class ReservaForm(forms.ModelForm):
    fecha = forms.DateField(
        label="Fecha", input_formats=[FORMATO_FECHA],
        widget=forms.DateInput(attrs={"type": "date"}, format=FORMATO_FECHA),
    )
    hora = forms.ChoiceField(label="Hora", choices=[(f"{t:%H:%M}", f"{t:%H:%M}") for t in franjas()])

    class Meta:
        model = Reserva
        fields = ("fecha", "hora", "personas", "mesa", "notas")
        widgets = {
            "personas": forms.NumberInput(attrs={"min": 1, "max": PERSONAS_MAX, "inputmode": "numeric"}),
            "mesa": forms.NumberInput(attrs={"min": MESA_MIN, "max": MESA_MAX, "inputmode": "numeric"}),
            "notas": forms.Textarea(attrs={"rows": 2, "maxlength": 200}),
        }

    def __init__(self, *args, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente = cliente
        hoy = timezone.localdate()
        self.fields["fecha"].widget.attrs.update(
            {"min": hoy.strftime(FORMATO_FECHA), "max": (hoy + timedelta(days=DIAS_MAX_ANTICIPACION)).strftime(FORMATO_FECHA)}
        )

    def clean_hora(self):
        return datetime.strptime(self.cleaned_data["hora"], "%H:%M").time()

    def clean_notas(self):
        return limpiar_espacios(self.cleaned_data.get("notas", ""))

    def clean(self):
        datos = super().clean()
        fecha, hora = datos.get("fecha"), datos.get("hora")
        if not fecha or not hora:
            return datos

        ahora = timezone.now()
        inicio = timezone.make_aware(datetime.combine(fecha, hora))
        if inicio < ahora + ANTICIPACION_MINIMA:
            self.add_error("fecha", "La reserva debe hacerse con al menos 1 hora de anticipación.")
        elif fecha > timezone.localdate() + timedelta(days=DIAS_MAX_ANTICIPACION):
            self.add_error("fecha", f"Solo se reserva con hasta {DIAS_MAX_ANTICIPACION} días de anticipación.")
        else:
            mesa = datos.get("mesa")
            if mesa:
                mesa_ocupada, cliente_ocupado = conflictos(mesa, fecha, hora, self.cliente)
                if mesa_ocupada:
                    self.add_error("mesa", f"La mesa {mesa} ya está reservada cerca de las {hora:%H:%M}. Elige otra mesa u otro horario.")
                elif cliente_ocupado:
                    raise forms.ValidationError("Ya tienes una reserva vigente que se cruza con este horario.")
        return datos


class FiltroReservaForm(forms.Form):
    estado = forms.ChoiceField(
        label="Estado", required=False,
        choices=[("", "Todas"), ("vigentes", "Vigentes")] + list(EstadoReserva.choices),
    )
    fecha = forms.DateField(
        label="Fecha", required=False, input_formats=[FORMATO_FECHA],
        widget=forms.DateInput(attrs={"type": "date"}, format=FORMATO_FECHA),
    )
    mesa = forms.IntegerField(
        label="Mesa", required=False, min_value=MESA_MIN, max_value=MESA_MAX,
        widget=forms.NumberInput(attrs={"min": MESA_MIN, "max": MESA_MAX}),
    )


class CambioEstadoReservaForm(forms.Form):
    """Estado que el usuario veía al pulsar el botón: evita acciones sobre datos desactualizados."""

    desde = forms.ChoiceField(choices=EstadoReserva.choices)
