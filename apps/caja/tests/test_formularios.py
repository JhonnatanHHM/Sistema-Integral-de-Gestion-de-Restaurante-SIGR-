from decimal import Decimal

from django.test import TestCase

from apps.caja.forms import CierreCajaForm, RangoFechasForm
from apps.caja.services import cerrar_caja
from apps.comun.forms import MontoField
from apps.pedidos.services import crear_pedido

from .base import DatosCajaMixin


class CierreCajaFormTests(DatosCajaMixin, TestCase):
    def datos(self, **cambios):
        base = {"fecha": "2026-11-10", "efectivo_contado": "150000", "observaciones": " Todo   en orden "}
        base.update(cambios)
        return base

    def test_cierre_valido_y_normalizado(self):
        form = CierreCajaForm(self.datos(efectivo_contado="150000,50"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["efectivo_contado"], Decimal("150000.50"))
        self.assertEqual(form.cleaned_data["observaciones"], "Todo en orden")

    def test_efectivo_cero_es_valido(self):
        self.assertTrue(CierreCajaForm(self.datos(efectivo_contado="0")).is_valid())

    def test_efectivo_invalido(self):
        for malo in ["-5", "abc", "1e3", "$100", "10.999", "12 500", "NaN", "Infinity", "12345678901", "", "' OR 1=1 --", "0; DROP TABLE caja_cierrecaja"]:
            with self.subTest(efectivo=malo):
                form = CierreCajaForm(self.datos(efectivo_contado=malo))
                self.assertFalse(form.is_valid())
                self.assertIn("efectivo_contado", form.errors)

    def test_efectivo_acepta_hasta_diez_digitos_enteros(self):
        self.assertTrue(CierreCajaForm(self.datos(efectivo_contado="9999999999.99")).is_valid())

    def test_fecha_invalida_o_futura(self):
        for mala in ["11/10/2026", "2026-02-30", "hoy", "", "2026-11-11", "2026-11-10' OR '1'='1"]:
            with self.subTest(fecha=mala):
                form = CierreCajaForm(self.datos(fecha=mala))
                self.assertFalse(form.is_valid())
                self.assertIn("fecha", form.errors)

    def test_fecha_ya_cerrada(self):
        cerrar_caja(self.pedido_cerrado().emitida.date(), Decimal("0"), "", self.admin)
        form = CierreCajaForm(self.datos())
        self.assertFalse(form.is_valid())
        self.assertIn("fecha", form.errors)

    def test_no_cierra_con_pedidos_sin_cerrar(self):
        crear_pedido(self.cliente, 2, "", [(self.pasta, 1)])
        form = CierreCajaForm(self.datos())
        self.assertFalse(form.is_valid())
        self.assertIn("sin cerrar", str(form.errors["fecha"]))

    def test_observaciones_peligrosas(self):
        self.assertIn("observaciones", CierreCajaForm(self.datos(observaciones="<script>x</script>")).errors)
        self.assertIn("observaciones", CierreCajaForm(self.datos(observaciones="x" * 201)).errors)


class RangoFechasFormTests(DatosCajaMixin, TestCase):
    def test_rango_valido(self):
        self.assertTrue(RangoFechasForm({"desde": "2026-11-01", "hasta": "2026-11-10"}).is_valid())
        self.assertTrue(RangoFechasForm({"desde": "2026-11-10", "hasta": "2026-11-10"}).is_valid())

    def test_rangos_invalidos(self):
        casos = [
            {"desde": "2026-11-10", "hasta": "2026-11-01"},      # al revés
            {"desde": "2026-11-01", "hasta": "2026-11-11"},      # futuro
            {"desde": "2025-01-01", "hasta": "2026-11-10"},      # más de un año
            {"desde": "01/11/2026", "hasta": "2026-11-10"},
            {"desde": "' OR 1=1 --", "hasta": "2026-11-10"},
            {"desde": "2026-11-01", "hasta": ""},
        ]
        for datos in casos:
            with self.subTest(datos=datos):
                self.assertFalse(RangoFechasForm(datos).is_valid())

    def test_un_anio_exacto_es_valido(self):
        self.assertTrue(RangoFechasForm({"desde": "2025-11-09", "hasta": "2026-11-10"}).is_valid())


class MontoFieldConfigurableTests(TestCase):
    def test_por_defecto_acepta_siete_enteros(self):
        campo = MontoField()
        self.assertEqual(campo.clean("9999999.99"), Decimal("9999999.99"))
        for malo in ["10000000", "12345678.9"]:
            with self.assertRaises(Exception):
                campo.clean(malo)
