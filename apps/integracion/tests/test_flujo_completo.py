"""Recorre el sistema de punta a punta, como lo harían las personas reales, a través de las vistas."""
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from apps.caja.models import CierreCaja, Factura
from apps.menu.models import Plato
from apps.pedidos.models import Estado, Pedido
from apps.reservas.models import EstadoReserva, Reserva
from apps.usuarios.models import Rol, Usuario

from .base import CLAVE, EntornoMixin


class FlujoCompletoTests(EntornoMixin, TestCase):
    def ingresar(self, correo):
        navegador = Client()
        respuesta = navegador.post(reverse("usuarios:login"), {"username": correo, "password": CLAVE})
        self.assertRedirects(respuesta, reverse("inicio"))
        return navegador

    def test_de_la_cuenta_nueva_hasta_el_reporte_de_ventas(self):
        # 1. Una persona nueva crea su cuenta y queda con sesión iniciada como cliente.
        cliente = Client()
        respuesta = cliente.post(reverse("usuarios:registro"), {
            "first_name": "Laura", "last_name": "Gómez", "email": "laura@ejemplo.com", "telefono": "300 123 4567",
            "password1": CLAVE, "password2": CLAVE,
        })
        self.assertRedirects(respuesta, reverse("inicio"))
        laura = Usuario.objects.get(email="laura@ejemplo.com")
        self.assertEqual((laura.rol, laura.telefono), (Rol.CLIENTE, "3001234567"))

        # 2. Ve la carta pública con los platos disponibles.
        self.assertContains(cliente.get(reverse("menu:publico")), "Bandeja paisa")

        # 3. Reserva una mesa y queda pendiente.
        respuesta = cliente.post(reverse("reservas:nueva"), {
            "fecha": "2026-11-12", "hora": "13:00", "personas": "4", "mesa": "6", "notas": "Cumpleaños",
        })
        self.assertRedirects(respuesta, reverse("reservas:lista"))
        reserva = Reserva.objects.get()
        self.assertEqual((reserva.cliente, reserva.estado), (laura, EstadoReserva.PENDIENTE))

        # 4. Hace un pedido: 2 bandejas y 1 limonada.
        bandeja = Plato.objects.get(nombre="Bandeja paisa")
        limonada = Plato.objects.get(nombre="Limonada de coco")
        respuesta = cliente.post(reverse("pedidos:nuevo"), {
            "mesa": "6", "notas": "Sin cebolla", f"plato_{bandeja.pk}": "2", f"plato_{limonada.pk}": "1",
        })
        pedido = Pedido.objects.get()
        self.assertRedirects(respuesta, reverse("pedidos:detalle", args=[pedido.pk]))
        self.assertEqual((pedido.cliente, pedido.estado, pedido.total), (laura, Estado.PENDIENTE, Decimal("77000")))

        # 5. El mesero confirma la reserva y lleva el pedido hasta cerrarlo.
        mesero = self.ingresar("mes@ejemplo.com")
        mesero.post(reverse("reservas:confirmar", args=[reserva.pk]), {"desde": "pendiente"})
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.CONFIRMADA)
        for esperado in ("en_preparacion", "listo", "servido", "cerrado"):
            pedido.refresh_from_db()
            mesero.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"desde": pedido.estado})
            pedido.refresh_from_db()
            self.assertEqual(pedido.estado, esperado)

        # 6. Al cerrarse el pedido se emitió su factura y la clienta puede verla.
        factura = Factura.objects.get()
        self.assertEqual((factura.pedido, factura.total, factura.emitida_por), (pedido, Decimal("77000"), self.mesero))
        self.assertContains(cliente.get(reverse("caja:factura", args=[factura.pk])), factura.numero)
        self.assertContains(cliente.get(reverse("pedidos:detalle", args=[pedido.pk])), "Ver factura")

        # 7. El mesero ve el total del día, pero no puede cerrar la caja ni ver reportes.
        resumen = mesero.get(reverse("caja:resumen"))
        self.assertEqual(resumen.context["total"], Decimal("77000"))
        self.assertEqual(mesero.get(reverse("caja:reportes")).status_code, 403)

        # 8. El administrador cierra la caja: el efectivo contado cuadra con las ventas.
        admin = self.ingresar("adm@ejemplo.com")
        respuesta = admin.post(reverse("caja:cierre_nuevo"), {"fecha": "2026-11-10", "efectivo_contado": "77000", "observaciones": ""})
        self.assertRedirects(respuesta, reverse("caja:cierres"))
        cierre = CierreCaja.objects.get()
        self.assertEqual((cierre.total_ventas, cierre.diferencia, cierre.resultado), (Decimal("77000"), Decimal("0"), "Cuadrado"))

        # 9. El reporte muestra la venta y el plato más vendido.
        reporte = admin.get(reverse("caja:reportes"))
        self.assertEqual((reporte.context["total"], reporte.context["facturas"]), (Decimal("77000"), 1))
        self.assertEqual(reporte.context["platos"][0]["plato__nombre"], "Bandeja paisa")
        self.assertEqual(reporte.context["platos"][0]["unidades"], 2)

        # 10. Con la caja cerrada ya no se pueden cerrar más pedidos ese día.
        otro = cliente.post(reverse("pedidos:nuevo"), {"mesa": "2", f"plato_{limonada.pk}": "1"})
        segundo = Pedido.objects.exclude(pk=pedido.pk).get()
        for _ in range(3):
            segundo.avanzar()
        mesero.post(reverse("pedidos:avanzar", args=[segundo.pk]), {"desde": "servido"})
        segundo.refresh_from_db()
        self.assertEqual(segundo.estado, Estado.SERVIDO)
        self.assertEqual(Factura.objects.count(), 1)

    def test_el_cliente_puede_cancelar_su_pedido_y_no_se_factura(self):
        cliente = self.ingresar("cli@ejemplo.com")
        bandeja = Plato.objects.get(nombre="Bandeja paisa")
        cliente.post(reverse("pedidos:nuevo"), {"mesa": "3", f"plato_{bandeja.pk}": "1"})
        pedido = Pedido.objects.get()
        cliente.post(reverse("pedidos:cancelar", args=[pedido.pk]))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Estado.CANCELADO)
        self.assertFalse(Factura.objects.exists())

    def test_un_administrador_da_de_alta_a_un_mesero_que_ya_puede_trabajar(self):
        admin = self.ingresar("adm@ejemplo.com")
        respuesta = admin.post(reverse("usuarios:personal_nuevo"), {
            "first_name": "Mario", "last_name": "Mesa", "email": "mario@ejemplo.com", "telefono": "",
            "password1": CLAVE, "password2": CLAVE, "rol": Rol.MESERO,
        })
        self.assertRedirects(respuesta, reverse("usuarios:lista"))
        mario = self.ingresar("mario@ejemplo.com")
        self.assertEqual(mario.get(reverse("menu:plato_lista")).status_code, 200)
        self.assertEqual(mario.get(reverse("usuarios:lista")).status_code, 403)

    def test_el_mesero_marca_un_plato_agotado_y_desaparece_de_la_carta_y_del_pedido(self):
        mesero = self.ingresar("mes@ejemplo.com")
        brownie = Plato.objects.get(nombre="Brownie con helado")
        mesero.post(reverse("menu:plato_disponibilidad", args=[brownie.pk]))
        self.assertNotContains(Client().get(reverse("menu:publico")), "Brownie con helado")
        cliente = self.ingresar("cli@ejemplo.com")
        cliente.post(reverse("pedidos:nuevo"), {"mesa": "1", f"plato_{brownie.pk}": "2"})
        self.assertFalse(Pedido.objects.exists())
