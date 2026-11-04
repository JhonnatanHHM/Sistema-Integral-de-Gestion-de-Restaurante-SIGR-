from django.test import TestCase
from django.urls import reverse

from apps.menu.models import Plato
from apps.pedidos.models import Estado, Pedido
from apps.pedidos.services import crear_pedido

from .base import DatosPedidosMixin


class CrearPedidoTests(DatosPedidosMixin, TestCase):
    def test_visitante_va_al_login(self):
        for nombre in ("pedidos:nuevo", "pedidos:lista"):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("usuarios:login"), r.url)

    def test_cliente_crea_su_pedido(self):
        self.client.force_login(self.cliente)
        r = self.client.post(reverse("pedidos:nuevo"), self.datos())
        pedido = Pedido.objects.get()
        self.assertRedirects(r, reverse("pedidos:detalle", args=[pedido.pk]))
        self.assertEqual((pedido.cliente, pedido.mesa, pedido.estado), (self.cliente, 5, Estado.PENDIENTE))
        self.assertEqual(pedido.items.count(), 2)

    def test_mesero_registra_pedido_de_mesa_sin_cliente(self):
        self.client.force_login(self.mesero)
        self.client.post(reverse("pedidos:nuevo"), self.datos())
        pedido = Pedido.objects.get()
        self.assertIsNone(pedido.cliente)
        self.assertEqual(pedido.creado_por, self.mesero)

    def test_pedido_invalido_no_se_guarda(self):
        self.client.force_login(self.cliente)
        for cambios in [{"mesa": "0"}, {"mesa": "abc"}, {f"plato_{self.pasta.pk}": "-3"}, {"notas": "<script>"}]:
            r = self.client.post(reverse("pedidos:nuevo"), self.datos(**cambios))
            self.assertEqual(r.status_code, 200)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_precio_siempre_viene_de_la_base(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("pedidos:nuevo"), self.datos(**{f"precio_{self.pasta.pk}": "1", "precio_unitario": "1"}))
        self.assertEqual(Pedido.objects.get().items.get(plato=self.pasta).precio_unitario, Plato.objects.get(pk=self.pasta.pk).precio)


class VisibilidadTests(DatosPedidosMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.mio = crear_pedido(self.cliente, 1, "", [(self.pasta, 1)])
        self.ajeno = crear_pedido(self.otro_cliente, 2, "", [(self.sopa, 1)])

    def test_cliente_solo_ve_sus_pedidos(self):
        self.client.force_login(self.cliente)
        r = self.client.get(reverse("pedidos:lista"))
        self.assertEqual([p.pk for p in r.context["pedidos"]], [self.mio.pk])
        self.assertEqual(self.client.get(reverse("pedidos:detalle", args=[self.mio.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("pedidos:detalle", args=[self.ajeno.pk])).status_code, 404)

    def test_cliente_no_cancela_pedido_ajeno(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(reverse("pedidos:cancelar", args=[self.ajeno.pk])).status_code, 404)
        self.ajeno.refresh_from_db()
        self.assertEqual(self.ajeno.estado, Estado.PENDIENTE)

    def test_personal_ve_todos(self):
        for usuario in (self.mesero, self.admin):
            self.client.force_login(usuario)
            r = self.client.get(reverse("pedidos:lista"))
            self.assertEqual({p.pk for p in r.context["pedidos"]}, {self.mio.pk, self.ajeno.pk})

    def test_filtros_y_su_validacion(self):
        self.client.force_login(self.mesero)
        r = self.client.get(reverse("pedidos:lista"), {"mesa": "2"})
        self.assertEqual([p.pk for p in r.context["pedidos"]], [self.ajeno.pk])
        r = self.client.get(reverse("pedidos:lista"), {"estado": "listo"})
        self.assertEqual(len(r.context["pedidos"]), 0)
        r = self.client.get(reverse("pedidos:lista"), {"estado": "activos"})
        self.assertEqual(len(r.context["pedidos"]), 2)

    def test_filtros_con_inyeccion_no_fallan_ni_devuelven_datos(self):
        self.client.force_login(self.mesero)
        for params in [{"estado": "' OR 1=1 --"}, {"mesa": "1; DROP TABLE pedidos_pedido"}, {"mesa": "-1"}]:
            r = self.client.get(reverse("pedidos:lista"), params)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.context["pedidos"]), 0)
        self.assertEqual(Pedido.objects.count(), 2)

    def test_respuesta_parcial_para_el_refresco_automatico(self):
        self.client.force_login(self.mesero)
        completa = self.client.get(reverse("pedidos:lista"))
        parcial = self.client.get(reverse("pedidos:lista"), {"parcial": "1"})
        self.assertContains(completa, "<html")
        self.assertNotContains(parcial, "<html")
        self.assertContains(parcial, f"#{self.mio.pk}")
        detalle = self.client.get(reverse("pedidos:detalle", args=[self.mio.pk]), {"parcial": "1"})
        self.assertNotContains(detalle, "<html")
        self.assertContains(detalle, "Pendiente")


class CambioDeEstadoTests(DatosPedidosMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.pedido = crear_pedido(self.cliente, 4, "", [(self.pasta, 1)])

    def avanzar(self, usuario, desde=None):
        self.client.force_login(usuario)
        return self.client.post(reverse("pedidos:avanzar", args=[self.pedido.pk]), {"desde": desde or self.pedido.estado})

    def test_cliente_no_puede_avanzar(self):
        self.assertEqual(self.avanzar(self.cliente).status_code, 403)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Estado.PENDIENTE)

    def test_visitante_no_puede_avanzar(self):
        r = self.client.post(reverse("pedidos:avanzar", args=[self.pedido.pk]), {"desde": "pendiente"})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("usuarios:login"), r.url)

    def test_avanzar_no_acepta_get(self):
        self.client.force_login(self.mesero)
        self.assertEqual(self.client.get(reverse("pedidos:avanzar", args=[self.pedido.pk])).status_code, 405)

    def test_mesero_recorre_el_flujo(self):
        for esperado in ("en_preparacion", "listo", "servido", "cerrado"):
            r = self.avanzar(self.mesero)
            self.assertRedirects(r, reverse("pedidos:detalle", args=[self.pedido.pk]))
            self.pedido.refresh_from_db()
            self.assertEqual(self.pedido.estado, esperado)
        r = self.avanzar(self.admin, desde="cerrado")
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Estado.CERRADO)

    def test_no_se_salta_pasos_si_la_pantalla_estaba_desactualizada(self):
        self.avanzar(self.mesero)                       # pendiente -> en_preparacion
        self.avanzar(self.admin, desde="pendiente")     # segundo clic con la pantalla vieja
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Estado.EN_PREPARACION)

    def test_estado_manipulado_se_rechaza(self):
        r = self.avanzar(self.mesero, desde="volando")
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Estado.PENDIENTE)
        self.assertEqual(r.status_code, 302)

    def test_cliente_cancela_su_pedido_pendiente_pero_no_uno_en_preparacion(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("pedidos:cancelar", args=[self.pedido.pk]))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Estado.CANCELADO)
        otro = crear_pedido(self.cliente, 4, "", [(self.sopa, 1)])
        otro.avanzar()
        self.client.post(reverse("pedidos:cancelar", args=[otro.pk]))
        otro.refresh_from_db()
        self.assertEqual(otro.estado, Estado.EN_PREPARACION)

    def test_cancelar_no_acepta_get(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("pedidos:cancelar", args=[self.pedido.pk])).status_code, 405)


class PlatoConPedidosTests(DatosPedidosMixin, TestCase):
    def test_no_se_elimina_un_plato_con_pedidos(self):
        crear_pedido(self.cliente, 1, "", [(self.pasta, 1)])
        self.client.force_login(self.admin)
        r = self.client.post(reverse("menu:plato_eliminar", args=[self.pasta.pk]), follow=True)
        self.assertTrue(Plato.objects.filter(pk=self.pasta.pk).exists())
        self.assertContains(r, "No se puede eliminar")
