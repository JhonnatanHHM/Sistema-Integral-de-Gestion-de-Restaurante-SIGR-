"""Formularios de cuentas. Cada campo se normaliza y valida antes de llegar a la base de datos."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.core.validators import RegexValidator

from .models import Rol, Usuario
from .validators import limpiar_espacios, normalizar_telefono


class NormalizacionPersonaMixin:
    """Limpieza común de nombre, apellido, correo y teléfono."""

    def clean_first_name(self):
        return limpiar_espacios(self.cleaned_data["first_name"])

    def clean_last_name(self):
        return limpiar_espacios(self.cleaned_data["last_name"])

    def clean_telefono(self):
        return normalizar_telefono(self.cleaned_data.get("telefono", ""))


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "placeholder": "correo@ejemplo.com"}),
    )

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class RegistroForm(NormalizacionPersonaMixin, UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "email", "telefono")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name", "maxlength": 60}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name", "maxlength": 60}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "correo@ejemplo.com"}),
            "telefono": forms.TextInput(attrs={"type": "tel", "inputmode": "tel", "autocomplete": "tel", "maxlength": 20, "placeholder": "+573001234567"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.", code="unique")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Rol.CLIENTE      # el registro público nunca crea personal ni administradores
        if commit:
            usuario.save()
        return usuario


class PersonalForm(RegistroForm):
    """Alta de personal (mesero o administrador) hecha por un administrador."""

    rol = forms.ChoiceField(label="Rol", choices=[(Rol.MESERO, "Mesero"), (Rol.ADMINISTRADOR, "Administrador")])

    class Meta(RegistroForm.Meta):
        fields = ("first_name", "last_name", "email", "telefono")

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = self.cleaned_data["rol"]
        if commit:
            usuario.save()
        return usuario


class PerfilForm(NormalizacionPersonaMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "telefono")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name", "maxlength": 60}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name", "maxlength": 60}),
            "telefono": forms.TextInput(attrs={"type": "tel", "inputmode": "tel", "autocomplete": "tel", "maxlength": 20}),
        }


class BusquedaUsuarioForm(forms.Form):
    """Filtros del listado de usuarios: solo caracteres de texto razonables, nunca se arma SQL con ellos."""

    q = forms.CharField(
        label="Buscar",
        required=False,
        max_length=100,
        validators=[RegexValidator(r"^[\w\s@.+'\-]*$", "La búsqueda contiene caracteres no permitidos.")],
        widget=forms.TextInput(attrs={"placeholder": "Nombre o correo", "maxlength": 100}),
    )
    rol = forms.ChoiceField(label="Rol", required=False, choices=[("", "Todos los roles")] + list(Rol.choices))

    def clean_q(self):
        return limpiar_espacios(self.cleaned_data["q"])


class AdminCreacionForm(NormalizacionPersonaMixin, UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("email", "first_name", "last_name", "telefono", "rol")


class AdminCambioForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"
