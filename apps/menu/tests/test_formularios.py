from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.comun.forms import MontoField
from apps.menu.forms import BusquedaMenuForm, BusquedaPlatoGestionForm, CategoriaForm, PlatoForm
from apps.menu.models import Categoria, Plato


class MontoFieldTests(TestCase):
    def test_valores_validos_se_normalizan(self):
        campo = MontoField()
        self.assertEqual(campo.clean("12500"), Decimal("12500"))
        self.assertEqual(campo.clean("12500,5"), Decimal("12500.5"))
        self.assertEqual(campo.clean(" 9.99 "), Decimal("9.99"))

    def test_valores_invalidos(self):
        campo = MontoField()
        for malo in ["abc", "-5", "0", "0.00", "1e3", "10.999", "99999999", "1,000.50", "12 500", "' OR 1=1 --", "NaN", "Infinity", "$100"]:
            with self.subTest(valor=malo):
                with self.assertRaises(ValidationError):
                    campo.clean(malo)


class CategoriaFormTests(TestCase):
    def test_valida_y_normaliza(self):
        form = CategoriaForm({"nombre": "  Platos   fuertes ", "descripcion": " Lo mejor ", "orden": "2", "activa": "on"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["nombre"], "Platos fuertes")

    def test_nombres_y_textos_peligrosos(self):
        for nombre in ["<script>alert(1)</script>", "x'; DROP TABLE menu_categoria;--", "a;b", "=cmd", "@"]:
            with self.subTest(nombre=nombre):
                self.assertFalse(CategoriaForm({"nombre": nombre, "orden": "1"}).is_valid())
        self.assertFalse(CategoriaForm({"nombre": "Ok", "descripcion": "<b>hola</b>", "orden": "1"}).is_valid())

    def test_orden_numerico_en_rango(self):
        for malo in ["abc", "-1", "1000", "1.5", ""]:
            with self.subTest(orden=malo):
                self.assertFalse(CategoriaForm({"nombre": "Ok", "orden": malo}).is_valid())

    def test_nombre_unico_sin_importar_mayusculas(self):
        Categoria.objects.create(nombre="Postres")
        self.assertFalse(CategoriaForm({"nombre": "POSTRES", "orden": "1"}).is_valid())

    def test_editar_misma_categoria_no_choca_consigo_misma(self):
        c = Categoria.objects.create(nombre="Postres")
        self.assertTrue(CategoriaForm({"nombre": "Postres", "orden": "1"}, instance=c).is_valid())


class PlatoFormTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Fuertes")

    def datos(self, **cambios):
        base = {"categoria": self.cat.pk, "nombre": "Bandeja paisa", "descripcion": "Con arepa", "precio": "34000", "disponible": "on"}
        base.update(cambios)
        return base

    def test_plato_valido(self):
        form = PlatoForm(self.datos(nombre="  Bandeja   paisa ", precio="34000,50"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["nombre"], "Bandeja paisa")
        self.assertEqual(form.cleaned_data["precio"], Decimal("34000.50"))

    def test_precio_invalido(self):
        for malo in ["abc", "-1", "0", "1e3", "10.999", "99999999", "", "'; DROP TABLE x;--"]:
            with self.subTest(precio=malo):
                form = PlatoForm(self.datos(precio=malo))
                self.assertFalse(form.is_valid())
                self.assertIn("precio", form.errors)

    def test_categoria_inexistente_inactiva_o_manipulada(self):
        inactiva = Categoria.objects.create(nombre="Oculta", activa=False)
        for malo in ["9999", "abc", "' OR 1=1", str(inactiva.pk), ""]:
            with self.subTest(categoria=malo):
                form = PlatoForm(self.datos(categoria=malo))
                self.assertFalse(form.is_valid())
                self.assertIn("categoria", form.errors)

    def test_nombre_y_descripcion_peligrosos(self):
        self.assertFalse(PlatoForm(self.datos(nombre="<img src=x onerror=alert(1)>")).is_valid())
        self.assertFalse(PlatoForm(self.datos(descripcion="<script>x</script>")).is_valid())
        self.assertFalse(PlatoForm(self.datos(nombre="x" * 101)).is_valid())
        self.assertFalse(PlatoForm(self.datos(descripcion="x" * 501)).is_valid())

    def test_nombre_repetido_en_la_misma_categoria(self):
        Plato.objects.create(categoria=self.cat, nombre="Bandeja paisa", precio="1000")
        form = PlatoForm(self.datos(nombre="BANDEJA PAISA"))
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_restricciones_de_base_de_datos(self):
        Plato.objects.create(categoria=self.cat, nombre="Sopa", precio="1000")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Plato.objects.create(categoria=self.cat, nombre="SOPA", precio="2000")
        with self.assertRaises(ValidationError):
            Plato(categoria=self.cat, nombre="Gratis", precio=Decimal("0")).full_clean()


class BusquedaFormTests(TestCase):
    def test_busquedas_peligrosas_se_rechazan(self):
        for q in ["' OR 1=1 --", "a; DROP TABLE x", "<script>", "a%b", "x" * 101]:
            with self.subTest(q=q):
                self.assertFalse(BusquedaMenuForm({"q": q}).is_valid())
                self.assertFalse(BusquedaPlatoGestionForm({"q": q}).is_valid())

    def test_categoria_y_disponibilidad_validadas(self):
        self.assertFalse(BusquedaMenuForm({"categoria": "99999"}).is_valid())
        self.assertFalse(BusquedaMenuForm({"categoria": "1 OR 1=1"}).is_valid())
        self.assertFalse(BusquedaPlatoGestionForm({"disponible": "talvez"}).is_valid())
        self.assertTrue(BusquedaPlatoGestionForm({"q": "pasta", "disponible": "1"}).is_valid())
