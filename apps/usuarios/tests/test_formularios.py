from django.test import TestCase

from apps.usuarios.forms import BusquedaUsuarioForm, LoginForm, PerfilForm, PersonalForm, RegistroForm
from apps.usuarios.models import Rol, Usuario

CLAVE = "Contr4seña-Muy-Segura!"


def datos(**cambios):
    base = {
        "first_name": "María José",
        "last_name": "O'Connor-Pérez",
        "email": "maria@ejemplo.com",
        "telefono": "+57 300-123-4567",
        "password1": CLAVE,
        "password2": CLAVE,
    }
    base.update(cambios)
    return base


class RegistroFormTests(TestCase):
    def test_datos_validos_se_normalizan(self):
        form = RegistroForm(datos(first_name="  María   José ", email="  MARIA@Ejemplo.COM "))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["first_name"], "María José")
        self.assertEqual(form.cleaned_data["email"], "maria@ejemplo.com")
        self.assertEqual(form.cleaned_data["telefono"], "+573001234567")

    def test_formatos_de_correo_invalidos(self):
        for malo in ["sin-arroba", "a@", "@b.com", "a b@c.com", "' OR '1'='1", "x@y.com'; DROP TABLE usuarios_usuario;--", "a" * 250 + "@b.com"]:
            with self.subTest(correo=malo):
                form = RegistroForm(datos(email=malo))
                self.assertFalse(form.is_valid())
                self.assertIn("email", form.errors)

    def test_nombres_solo_letras(self):
        for malo in ["Ana1", "<script>alert(1)</script>", "Robert'); DROP TABLE x;--", "Ana_Maria", "12345", "A" * 61]:
            with self.subTest(nombre=malo):
                form = RegistroForm(datos(first_name=malo))
                self.assertFalse(form.is_valid())
                self.assertIn("first_name", form.errors)

    def test_telefono_formato(self):
        for malo in ["abc", "12", "+1234567890123456", "300-ABC-1234", "1; DROP TABLE"]:
            with self.subTest(telefono=malo):
                form = RegistroForm(datos(telefono=malo))
                self.assertFalse(form.is_valid())
                self.assertIn("telefono", form.errors)

    def test_telefono_es_opcional(self):
        self.assertTrue(RegistroForm(datos(telefono="")).is_valid())

    def test_correo_duplicado_ignora_mayusculas(self):
        Usuario.objects.create_user("maria@ejemplo.com", CLAVE, first_name="M", last_name="J")
        form = RegistroForm(datos(email="MARIA@EJEMPLO.COM"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_claves_distintas_o_debiles(self):
        self.assertFalse(RegistroForm(datos(password2="otra")).is_valid())
        self.assertFalse(RegistroForm(datos(password1="12345678", password2="12345678")).is_valid())

    def test_siempre_crea_cliente_aunque_envien_rol(self):
        form = RegistroForm(datos(rol=Rol.ADMINISTRADOR, is_superuser="on", is_staff="on"))
        self.assertTrue(form.is_valid(), form.errors)
        usuario = form.save()
        self.assertEqual(usuario.rol, Rol.CLIENTE)
        self.assertFalse(usuario.is_staff or usuario.is_superuser)


class PersonalFormTests(TestCase):
    def test_rol_solo_mesero_o_administrador(self):
        self.assertTrue(PersonalForm(datos(rol=Rol.MESERO)).is_valid())
        self.assertFalse(PersonalForm(datos(rol=Rol.CLIENTE)).is_valid())
        self.assertFalse(PersonalForm(datos(rol="superjefe")).is_valid())
        self.assertFalse(PersonalForm(datos()).is_valid())


class PerfilFormTests(TestCase):
    def test_no_permite_cambiar_correo_ni_rol(self):
        self.assertEqual(list(PerfilForm().fields), ["first_name", "last_name", "telefono"])


class LoginFormTests(TestCase):
    def test_exige_formato_de_correo(self):
        form = LoginForm(data={"username": "' OR 1=1 --", "password": "x"})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


class BusquedaFormTests(TestCase):
    def test_busqueda_valida(self):
        form = BusquedaUsuarioForm({"q": "  ana   pérez ", "rol": Rol.MESERO})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["q"], "ana pérez")

    def test_busqueda_rechaza_caracteres_peligrosos_y_roles_invalidos(self):
        for malo in ["' OR 1=1 --", "a; DROP TABLE x", "<script>", "a%b", "x" * 101]:
            with self.subTest(q=malo):
                self.assertFalse(BusquedaUsuarioForm({"q": malo}).is_valid())
        self.assertFalse(BusquedaUsuarioForm({"rol": "hacker"}).is_valid())
