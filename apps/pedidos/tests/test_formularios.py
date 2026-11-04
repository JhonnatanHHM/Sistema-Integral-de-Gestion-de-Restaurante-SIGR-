from django.test import TestCase

from apps.pedidos.forms import CambioEstadoForm, FiltroPedidoForm, PedidoForm

from .base import DatosPedidosMixin


class PedidoFormTests(DatosPedidosMixin, TestCase):
    def test_pedido_valido(self):
        form = PedidoForm(self.datos(notas="  Sin   cebolla "))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["mesa"], 5)
        self.assertEqual(form.cleaned_data["notas"], "Sin cebolla")
        self.assertEqual([(p.nombre, c) for p, c in form.items], [("Pasta alfredo", 2), ("Sopa", 1)])

    def test_mesa_invalida(self):
        for mala in ["0", "100", "-1", "abc", "1.5", "", "5; DROP TABLE pedidos_pedido", "' OR 1=1"]:
            with self.subTest(mesa=mala):
                form = PedidoForm(self.datos(mesa=mala))
                self.assertFalse(form.is_valid())
                self.assertIn("mesa", form.errors)

    def test_cantidades_invalidas(self):
        for mala in ["-1", "51", "abc", "1.5", "1e1", "2; DROP TABLE x"]:
            with self.subTest(cantidad=mala):
                form = PedidoForm(self.datos(**{f"plato_{self.pasta.pk}": mala}))
                self.assertFalse(form.is_valid())
                self.assertIn(f"plato_{self.pasta.pk}", form.errors)

    def test_exige_al_menos_un_plato(self):
        form = PedidoForm({"mesa": "5", f"plato_{self.pasta.pk}": "0", f"plato_{self.sopa.pk}": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("al menos un plato", str(form.non_field_errors()))

    def test_platos_no_disponibles_o_de_categorias_ocultas_se_ignoran(self):
        form = PedidoForm(self.datos(**{f"plato_{self.agotado.pk}": "3", f"plato_{self.secreto.pk}": "3", "plato_99999": "1"}))
        self.assertTrue(form.is_valid())
        self.assertEqual({p.nombre for p, _ in form.items}, {"Pasta alfredo", "Sopa"})
        self.assertNotIn(f"plato_{self.agotado.pk}", form.fields)

    def test_el_precio_enviado_por_el_navegador_se_ignora(self):
        form = PedidoForm(self.datos(precio="1", **{f"precio_{self.pasta.pk}": "1"}))
        self.assertTrue(form.is_valid())
        self.assertNotIn("precio", form.cleaned_data)

    def test_notas_peligrosas(self):
        self.assertFalse(PedidoForm(self.datos(notas="<script>alert(1)</script>")).is_valid())
        self.assertFalse(PedidoForm(self.datos(notas="x" * 201)).is_valid())


class FiltrosFormTests(TestCase):
    def test_filtro_valido(self):
        self.assertTrue(FiltroPedidoForm({"estado": "activos", "mesa": "7"}).is_valid())
        self.assertTrue(FiltroPedidoForm({"estado": "en_preparacion"}).is_valid())

    def test_filtro_invalido(self):
        for datos in [{"estado": "hackeado"}, {"estado": "' OR 1=1"}, {"mesa": "0"}, {"mesa": "100"}, {"mesa": "x"}]:
            with self.subTest(datos=datos):
                self.assertFalse(FiltroPedidoForm(datos).is_valid())

    def test_cambio_de_estado_solo_acepta_estados_conocidos(self):
        self.assertTrue(CambioEstadoForm({"desde": "pendiente"}).is_valid())
        self.assertFalse(CambioEstadoForm({"desde": "volando"}).is_valid())
        self.assertFalse(CambioEstadoForm({}).is_valid())
