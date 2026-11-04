from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.caja.models import CierreCaja, Factura
from apps.pedidos.models import Estado, Pedido
from apps.pedidos.services import crear_pedido

from .base import HOY, DatosCajaMixin


class PermisosTests(DatosCajaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.factura = self.pedido_cerrado()
        self.urls_admin = [reverse(n) for n in ("caja:cierre_nuevo", "caja:cierres", "caja:reportes", "caja:facturas")]

    def test_visitante_va_al_login(self):
        for url in [reverse("caja:resumen")] + self.urls_admin + [reverse("caja:factura", args=[self.factura.pk])]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn(reverse("usuarios:login"), r.url)

    def test_cliente_no_entra_a_caja(self):
        self.client.force_login(self.cliente)
        for url in [reverse("caja:resumen")] + self.urls_admin:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_mesero_solo_ve_el_resumen(self):
        self.client.force_login(self.mesero)
        self.assertEqual(self.client.get(reverse("caja:resumen")).status_code, 200)
        for url in self.urls_admin:
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.assertEqual(self.client.post(reverse("caja:cierre_nuevo"), {"fecha": "2026-11-10", "efectivo_contado": "1"}).status_code, 403)

    def test_resumen_del_mesero_muestra_el_total_sin_detalle(self):
        self.client.force_login(self.mesero)
        r = self.client.get(reverse("caja:resumen"))
        self.assertContains(r, "Ventas del día")
        self.assertNotContains(r, "Facturas emitidas")
        self.assertNotContains(r, "Cerrar caja")

    def test_administrador_accede_a_todo(self):
        self.client.force_login(self.admin)
        for url in [reverse("caja:resumen")] + self.urls_admin:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_cierres_no_tienen_rutas_de_edicion_ni_borrado(self):
        self.client.force_login(self.admin)
        for url in ("/caja/cierres/1/editar/", "/caja/cierres/1/eliminar/"):
            self.assertEqual(self.client.get(url).status_code, 404)


class FacturaVisibilidadTests(DatosCajaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.mia = self.pedido_cerrado(cliente=self.cliente)
        self.ajena = self.pedido_cerrado(cliente=self.otro_cliente)

    def test_cliente_ve_solo_su_factura(self):
        self.client.force_login(self.cliente)
        self.assertContains(self.client.get(reverse("caja:factura", args=[self.mia.pk])), self.mia.numero)
        self.assertEqual(self.client.get(reverse("caja:factura", args=[self.ajena.pk])).status_code, 404)

    def test_personal_ve_cualquiera(self):
        for usuario in (self.mesero, self.admin):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(reverse("caja:factura", args=[self.ajena.pk])).status_code, 200)

    def test_el_detalle_del_pedido_enlaza_la_factura(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse("pedidos:detalle", args=[self.mia.pedido_id]))
        self.assertContains(r, reverse("caja:factura", args=[self.mia.pk]))


class FacturacionAlCerrarPedidoTests(DatosCajaMixin, TestCase):
    def avanzar(self, pedido):
        return self.client.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"desde": pedido.estado})

    def test_al_cerrar_el_pedido_se_emite_la_factura_una_sola_vez(self):
        pedido = crear_pedido(self.cliente, 1, "", [(self.pasta, 2)])
        self.client.force_login(self.mesero)
        for _ in range(3):
            self.avanzar(pedido); pedido.refresh_from_db()
        self.assertFalse(Factura.objects.exists())
        self.avanzar(pedido); pedido.refresh_from_db()       # servido -> cerrado
        self.assertEqual(pedido.estado, Estado.CERRADO)
        factura = Factura.objects.get()
        self.assertEqual((factura.pedido, factura.total, factura.emitida_por), (pedido, Decimal("56000"), self.mesero))
        self.avanzar(pedido)                                  # ya cerrado: no duplica
        self.assertEqual(Factura.objects.count(), 1)

    def test_con_la_caja_cerrada_no_se_pueden_cerrar_pedidos(self):
        pedido = crear_pedido(self.cliente, 1, "", [(self.pasta, 1)])
        for _ in range(3):
            pedido.avanzar()                                  # queda servido
        CierreCaja.objects.create(
            fecha=HOY, total_ventas=0, numero_facturas=0, efectivo_contado=0, diferencia=0, cerrado_por=self.admin
        )
        self.client.force_login(self.mesero)
        r = self.client.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"desde": "servido"}, follow=True)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Estado.SERVIDO)
        self.assertFalse(Factura.objects.exists())
        self.assertContains(r, "caja de hoy ya está cerrada")


class CierreDeCajaViewTests(DatosCajaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.pedido_cerrado()                                 # 65.500,50 hoy
        self.client.force_login(self.admin)

    def test_cerrar_caja(self):
        r = self.client.post(reverse("caja:cierre_nuevo"), {"fecha": "2026-11-10", "efectivo_contado": "65000", "observaciones": "Faltaron 500"})
        self.assertRedirects(r, reverse("caja:cierres"))
        cierre = CierreCaja.objects.get()
        self.assertEqual((cierre.total_ventas, cierre.diferencia, cierre.resultado, cierre.cerrado_por), (Decimal("65500.50"), Decimal("-500.50"), "Faltante", self.admin))

    def test_no_se_cierra_dos_veces_el_mismo_dia(self):
        datos = {"fecha": "2026-11-10", "efectivo_contado": "65500.50"}
        self.client.post(reverse("caja:cierre_nuevo"), datos)
        r = self.client.post(reverse("caja:cierre_nuevo"), datos)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(CierreCaja.objects.count(), 1)
        self.assertContains(r, "ya fue cerrada")

    def test_datos_invalidos_no_cierran(self):
        for datos in [{"fecha": "2026-11-10", "efectivo_contado": "-1"}, {"fecha": "2026-11-10", "efectivo_contado": "abc"}, {"fecha": "mañana", "efectivo_contado": "1"}]:
            self.assertEqual(self.client.post(reverse("caja:cierre_nuevo"), datos).status_code, 200)
        self.assertEqual(CierreCaja.objects.count(), 0)

    def test_total_y_diferencia_no_se_aceptan_del_formulario(self):
        self.client.post(reverse("caja:cierre_nuevo"), {"fecha": "2026-11-10", "efectivo_contado": "65500.50", "total_ventas": "1", "diferencia": "999", "cerrado_por": self.mesero.pk})
        cierre = CierreCaja.objects.get()
        self.assertEqual((cierre.total_ventas, cierre.diferencia, cierre.cerrado_por), (Decimal("65500.50"), Decimal("0"), self.admin))

    def test_resumen_refleja_el_cierre(self):
        self.client.post(reverse("caja:cierre_nuevo"), {"fecha": "2026-11-10", "efectivo_contado": "65500.50"})
        self.assertContains(self.client.get(reverse("caja:resumen")), "ya está cerrada")


class ReporteViewTests(DatosCajaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.pedido_cerrado(dia=9)
        self.pedido_cerrado()
        self.client.force_login(self.admin)

    def test_reporte_por_defecto_cubre_los_ultimos_siete_dias(self):
        r = self.client.get(reverse("caja:reportes"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.context["facturas"], r.context["total"]), (2, Decimal("131001.00")))
        self.assertEqual(r.context["ticket_promedio"], Decimal("65500.50"))

    def test_reporte_con_rango(self):
        r = self.client.get(reverse("caja:reportes"), {"desde": "2026-11-10", "hasta": "2026-11-10"})
        self.assertEqual((r.context["facturas"], r.context["total"]), (1, Decimal("65500.50")))
        self.assertEqual([p["plato__nombre"] for p in r.context["platos"]], ["Pasta", "Sopa"])

    def test_reporte_con_parametros_invalidos_o_inyeccion(self):
        for params in [{"desde": "' OR 1=1 --", "hasta": "2026-11-10"}, {"desde": "2026-11-10", "hasta": "2026-11-01"}, {"desde": "2020-01-01", "hasta": "2026-11-10"}, {"desde": "x; DROP TABLE caja_factura", "hasta": "y"}]:
            r = self.client.get(reverse("caja:reportes"), params)
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.context["formulario"].errors)
            self.assertNotIn("dias", r.context)
        self.assertEqual(Factura.objects.count(), 2)

    def test_listado_de_facturas(self):
        r = self.client.get(reverse("caja:facturas"))
        self.assertEqual(len(r.context["facturas"]), 2)
