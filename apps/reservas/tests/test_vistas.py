from datetime import time

from django.test import TestCase
from django.urls import reverse

from apps.reservas.models import EstadoReserva, Reserva

from .base import DatosReservasMixin


class CrearReservaTests(DatosReservasMixin, TestCase):
    def test_visitante_va_al_login(self):
        for nombre in ("reservas:nueva", "reservas:lista"):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("usuarios:login"), r.url)

    def test_el_personal_no_crea_reservas(self):
        for usuario in (self.mesero, self.admin):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(reverse("reservas:nueva")).status_code, 403)
            self.assertEqual(self.client.post(reverse("reservas:nueva"), self.datos()).status_code, 403)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_cliente_crea_reserva_pendiente_a_su_nombre(self):
        self.client.force_login(self.cliente)
        r = self.client.post(reverse("reservas:nueva"), self.datos())
        self.assertRedirects(r, reverse("reservas:lista"))
        reserva = Reserva.objects.get()
        self.assertEqual((reserva.cliente, reserva.estado, reserva.mesa, reserva.personas), (self.cliente, EstadoReserva.PENDIENTE, 7, 4))

    def test_el_cliente_y_el_estado_no_se_aceptan_del_formulario(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("reservas:nueva"), self.datos(cliente=self.otro_cliente.pk, estado="confirmada"))
        reserva = Reserva.objects.get()
        self.assertEqual((reserva.cliente, reserva.estado), (self.cliente, EstadoReserva.PENDIENTE))

    def test_datos_invalidos_no_guardan(self):
        self.client.force_login(self.cliente)
        for cambios in [{"hora": "10:00"}, {"fecha": "ayer"}, {"personas": "99"}, {"mesa": "0"}, {"notas": "<b>x</b>"}, {"fecha": "2026-01-01"}]:
            r = self.client.post(reverse("reservas:nueva"), self.datos(**cambios))
            self.assertEqual(r.status_code, 200, cambios)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_no_se_reserva_una_mesa_ocupada(self):
        self.reservar(cliente=self.otro_cliente, dia=11, hora=time(13, 0), mesa=7)
        self.client.force_login(self.cliente)
        r = self.client.post(reverse("reservas:nueva"), self.datos(hora="14:00"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "ya está reservada")
        self.assertEqual(Reserva.objects.count(), 1)


class VisibilidadTests(DatosReservasMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.mia = self.reservar(cliente=self.cliente, dia=11, mesa=1)
        self.ajena = self.reservar(cliente=self.otro_cliente, dia=12, mesa=2)

    def test_cliente_solo_ve_las_suyas(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse("reservas:lista"))
        self.assertEqual([x.pk for x in r.context["reservas"]], [self.mia.pk])

    def test_personal_ve_todas(self):
        for usuario in (self.mesero, self.admin):
            self.client.force_login(usuario)
            r = self.client.get(reverse("reservas:lista"))
            self.assertEqual({x.pk for x in r.context["reservas"]}, {self.mia.pk, self.ajena.pk})

    def test_filtros(self):
        self.client.force_login(self.mesero)
        self.assertEqual([x.pk for x in self.client.get(reverse("reservas:lista"), {"mesa": "2"}).context["reservas"]], [self.ajena.pk])
        self.assertEqual([x.pk for x in self.client.get(reverse("reservas:lista"), {"fecha": "2026-11-11"}).context["reservas"]], [self.mia.pk])
        self.ajena.cancelar()
        self.assertEqual([x.pk for x in self.client.get(reverse("reservas:lista"), {"estado": "vigentes"}).context["reservas"]], [self.mia.pk])

    def test_filtros_con_inyeccion_devuelven_vacio_sin_error(self):
        self.client.force_login(self.mesero)
        for params in [{"estado": "' OR 1=1 --"}, {"fecha": "2026-11-11' OR '1'='1"}, {"mesa": "1; DROP TABLE reservas_reserva"}, {"mesa": "-1"}]:
            r = self.client.get(reverse("reservas:lista"), params)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.context["reservas"]), 0)
        self.assertEqual(Reserva.objects.count(), 2)

    def test_respuesta_parcial(self):
        self.client.force_login(self.mesero)
        self.assertContains(self.client.get(reverse("reservas:lista")), "<html")
        self.assertNotContains(self.client.get(reverse("reservas:lista"), {"parcial": "1"}), "<html")


class CambioDeEstadoTests(DatosReservasMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.reserva = self.reservar(cliente=self.cliente)

    def post(self, usuario, nombre, desde=None, pk=None):
        self.client.force_login(usuario)
        return self.client.post(reverse(nombre, args=[pk or self.reserva.pk]), {"desde": desde or self.reserva.estado})

    def test_cliente_no_confirma_ni_completa(self):
        for nombre in ("reservas:confirmar", "reservas:completar"):
            self.assertEqual(self.post(self.cliente, nombre).status_code, 403)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, EstadoReserva.PENDIENTE)

    def test_visitante_no_puede(self):
        r = self.client.post(reverse("reservas:confirmar", args=[self.reserva.pk]), {"desde": "pendiente"})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("usuarios:login"), r.url)

    def test_personal_confirma_y_completa(self):
        self.post(self.mesero, "reservas:confirmar")
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, EstadoReserva.CONFIRMADA)
        self.post(self.admin, "reservas:completar")
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, EstadoReserva.COMPLETADA)

    def test_no_se_completa_una_pendiente(self):
        self.post(self.mesero, "reservas:completar")
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, EstadoReserva.PENDIENTE)

    def test_pantalla_desactualizada_o_estado_manipulado(self):
        self.post(self.mesero, "reservas:confirmar")
        self.post(self.admin, "reservas:cancelar", desde="pendiente")    # pantalla vieja
        self.post(self.admin, "reservas:completar", desde="volando")      # valor inventado
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, EstadoReserva.CONFIRMADA)

    def test_cliente_cancela_la_suya_pero_no_la_ajena(self):
        ajena = self.reservar(cliente=self.otro_cliente, dia=12, mesa=9)
        self.assertEqual(self.post(self.cliente, "reservas:cancelar", pk=ajena.pk).status_code, 404)
        ajena.refresh_from_db()
        self.assertEqual(ajena.estado, EstadoReserva.PENDIENTE)
        self.post(self.cliente, "reservas:cancelar")
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, EstadoReserva.CANCELADA)

    def test_personal_cancela_cualquiera_y_una_cancelada_queda_firme(self):
        self.post(self.mesero, "reservas:cancelar")
        self.post(self.mesero, "reservas:confirmar", desde="cancelada")
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, EstadoReserva.CANCELADA)

    def test_las_acciones_no_aceptan_get(self):
        self.client.force_login(self.mesero)
        for nombre in ("reservas:confirmar", "reservas:completar", "reservas:cancelar"):
            self.assertEqual(self.client.get(reverse(nombre, args=[self.reserva.pk])).status_code, 405)

    def test_cancelar_libera_la_mesa(self):
        self.client.force_login(self.otro_cliente)
        datos = self.datos(mesa=str(self.reserva.mesa), hora="14:00")
        self.assertEqual(self.client.post(reverse("reservas:nueva"), datos).status_code, 200)
        self.reserva.cancelar()
        self.assertRedirects(self.client.post(reverse("reservas:nueva"), datos), reverse("reservas:lista"))
