from datetime import datetime, time
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.reservas.forms import CambioEstadoReservaForm, FiltroReservaForm, ReservaForm

from .base import DatosReservasMixin


class ReservaFormTests(DatosReservasMixin, TestCase):
    def form(self, **cambios):
        return ReservaForm(self.datos(**cambios), cliente=self.cliente)

    def test_reserva_valida(self):
        form = self.form(notas="  Cumpleaños   de Ana ")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["hora"], time(13, 0))
        self.assertEqual(form.cleaned_data["notas"], "Cumpleaños de Ana")

    def test_horas_fuera_de_las_franjas(self):
        for mala in ["10:30", "20:30", "21:00", "13:15", "25:00", "13:00:00", "abc", "", "13:00'; DROP TABLE x"]:
            with self.subTest(hora=mala):
                form = self.form(hora=mala)
                self.assertFalse(form.is_valid())
                self.assertIn("hora", form.errors)

    def test_formatos_de_fecha_invalidos(self):
        for mala in ["11/11/2026", "2026-02-30", "2026-13-01", "mañana", "", "2026-11-11; DROP TABLE x", "20261111"]:
            with self.subTest(fecha=mala):
                form = self.form(fecha=mala)
                self.assertFalse(form.is_valid())
                self.assertIn("fecha", form.errors)

    def test_fecha_pasada_o_muy_proxima(self):
        self.assertIn("fecha", self.form(fecha="2026-11-09").errors)
        self.assertTrue(self.form(fecha="2026-11-10", hora="11:00").is_valid())         # son las 9:00: faltan 2 horas
        mas_tarde = timezone.make_aware(datetime(2026, 11, 10, 10, 30))
        with patch("django.utils.timezone.now", return_value=mas_tarde):
            self.assertIn("fecha", self.form(fecha="2026-11-10", hora="11:00").errors)   # solo faltan 30 minutos
            self.assertTrue(self.form(fecha="2026-11-10", hora="11:30").is_valid())      # justo 1 hora

    def test_limite_de_anticipacion(self):
        self.assertTrue(self.form(fecha="2026-12-10").is_valid())        # exactamente 30 días
        self.assertIn("fecha", self.form(fecha="2026-12-11").errors)     # 31 días

    def test_personas_y_mesa_invalidas(self):
        for campo, malos in {"personas": ["0", "13", "-2", "abc", "1.5", ""], "mesa": ["0", "100", "-1", "x", "1.5", ""]}.items():
            for malo in malos:
                with self.subTest(campo=campo, valor=malo):
                    form = self.form(**{campo: malo})
                    self.assertFalse(form.is_valid())
                    self.assertIn(campo, form.errors)

    def test_notas_peligrosas(self):
        self.assertIn("notas", self.form(notas="<script>alert(1)</script>").errors)
        self.assertIn("notas", self.form(notas="x" * 201).errors)

    def test_mesa_ocupada_se_informa_en_el_campo_mesa(self):
        self.reservar(dia=11, hora=time(13, 0), mesa=7)
        form = self.form(hora="14:00")
        self.assertFalse(form.is_valid())
        self.assertIn("mesa", form.errors)
        self.assertTrue(self.form(hora="15:00").is_valid())

    def test_cliente_con_reserva_cruzada(self):
        self.reservar(dia=11, hora=time(13, 0), mesa=1)
        form = self.form(hora="14:00", mesa="9")
        self.assertFalse(form.is_valid())
        self.assertIn("se cruza", str(form.non_field_errors()))

    def test_widget_de_fecha_limita_el_rango(self):
        attrs = ReservaForm(cliente=self.cliente).fields["fecha"].widget.attrs
        self.assertEqual((attrs["min"], attrs["max"]), ("2026-11-10", "2026-12-10"))


class FiltrosTests(TestCase):
    def test_filtros_validos_e_invalidos(self):
        self.assertTrue(FiltroReservaForm({"estado": "vigentes", "fecha": "2026-11-11", "mesa": "4"}).is_valid())
        for datos in [{"estado": "x"}, {"fecha": "11/11/2026"}, {"fecha": "' OR 1=1"}, {"mesa": "0"}, {"mesa": "1; DROP TABLE x"}]:
            with self.subTest(datos=datos):
                self.assertFalse(FiltroReservaForm(datos).is_valid())

    def test_cambio_de_estado(self):
        self.assertTrue(CambioEstadoReservaForm({"desde": "pendiente"}).is_valid())
        self.assertFalse(CambioEstadoReservaForm({"desde": "volando"}).is_valid())
