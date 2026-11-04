from django import forms
from django.core.validators import RegexValidator

from apps.comun.forms import MontoField
from apps.comun.validators import limpiar_espacios

from .models import Categoria, Plato


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ("nombre", "descripcion", "orden", "activa")
        widgets = {
            "nombre": forms.TextInput(attrs={"maxlength": 60}),
            "descripcion": forms.TextInput(attrs={"maxlength": 200}),
            "orden": forms.NumberInput(attrs={"min": 0, "max": 999}),
        }

    def clean_nombre(self):
        nombre = limpiar_espacios(self.cleaned_data["nombre"])
        repetidas = Categoria.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise forms.ValidationError("Ya existe una categoría con este nombre.", code="unique")
        return nombre

    def clean_descripcion(self):
        return limpiar_espacios(self.cleaned_data.get("descripcion", ""))


class PlatoForm(forms.ModelForm):
    class Meta:
        model = Plato
        fields = ("categoria", "nombre", "descripcion", "precio", "imagen", "disponible", "destacado")
        field_classes = {"precio": MontoField}
        widgets = {
            "nombre": forms.TextInput(attrs={"maxlength": 100}),
            "descripcion": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
            "imagen": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }
        help_texts = {"imagen": "JPG, PNG o WebP de hasta 2 MB y 4000 px por lado."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        activas = Categoria.objects.filter(activa=True)
        if self.instance.pk:
            activas = Categoria.objects.filter(activa=True) | Categoria.objects.filter(pk=self.instance.categoria_id)
        self.fields["categoria"].queryset = activas.distinct()
        self.fields["categoria"].empty_label = "Selecciona una categoría"

    def clean_nombre(self):
        return limpiar_espacios(self.cleaned_data["nombre"])

    def clean_descripcion(self):
        return limpiar_espacios(self.cleaned_data.get("descripcion", ""))

    def clean(self):
        datos = super().clean()
        categoria, nombre = datos.get("categoria"), datos.get("nombre")
        if categoria and nombre:
            repetidos = Plato.objects.filter(categoria=categoria, nombre__iexact=nombre).exclude(pk=self.instance.pk)
            if repetidos.exists():
                self.add_error("nombre", "Ya existe un plato con este nombre en la categoría.")
        return datos


_validar_busqueda = RegexValidator(r"^[\w\s@.+'\-]*$", "La búsqueda contiene caracteres no permitidos.")


class BusquedaMenuForm(forms.Form):
    """Búsqueda del menú público: solo platos disponibles de categorías activas."""

    q = forms.CharField(
        label="Buscar",
        required=False,
        max_length=100,
        validators=[_validar_busqueda],
        widget=forms.TextInput(attrs={"placeholder": "Buscar plato", "maxlength": 100}),
    )
    categoria = forms.ModelChoiceField(
        label="Categoría", required=False, queryset=Categoria.objects.filter(activa=True), empty_label="Todas"
    )

    def clean_q(self):
        return limpiar_espacios(self.cleaned_data["q"])


class BusquedaPlatoGestionForm(BusquedaMenuForm):
    """Búsqueda del personal: incluye platos no disponibles y todas las categorías."""

    disponible = forms.ChoiceField(
        label="Disponibilidad",
        required=False,
        choices=[("", "Todos"), ("1", "Disponibles"), ("0", "No disponibles")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.all()
