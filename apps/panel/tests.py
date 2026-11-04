from django.test import Client, TestCase
from django.urls import reverse

from apps.menu.models import Categoria, Plato
from apps.menu.tests.test_imagenes import MediaTemporalMixin, subida
from apps.usuarios.models import Rol, Usuario

CLAVE = "Contr4seña-Muy-Segura!"


def sesion(rol):
    usuario = Usuario.objects.create_user(f"{rol}@ejemplo.com", CLAVE, first_name="Nombre", last_name="Apellido", rol=rol)
    navegador = Client()
    navegador.force_login(usuario)
    return navegador


class InicioTests(TestCase):
    def test_inicio_responde_200(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "SIGR")

    def test_el_inicio_ya_no_muestra_las_tarjetas_de_modulos_internos(self):
        pagina = self.client.get(reverse("inicio")).content.decode()
        for texto in ("Caja y reportes", "Cierre de caja y ventas diarias", "Registro y seguimiento en tiempo real"):
            self.assertNotIn(texto, pagina)


class InicioPorRolTests(TestCase):
    def enlaces(self, navegador):
        pagina = navegador.get(reverse("inicio")).content.decode()
        portada = pagina.split('class="portada__acciones"')[1].split("</section>")[0]
        return portada

    def test_visitante_ve_menu_registro_e_ingreso(self):
        portada = self.enlaces(self.client)
        self.assertIn(reverse("menu:publico"), portada)
        self.assertIn(reverse("usuarios:registro"), portada)
        self.assertIn(reverse("usuarios:login"), portada)
        for ruta in ("caja:resumen", "menu:plato_lista", "usuarios:lista", "pedidos:lista"):
            self.assertNotIn(reverse(ruta), portada)

    def test_cliente_ve_menu_pedido_y_reserva_pero_nada_de_gestion(self):
        portada = self.enlaces(sesion(Rol.CLIENTE))
        for ruta in ("menu:publico", "pedidos:nuevo", "reservas:nueva"):
            self.assertIn(reverse(ruta), portada)
        for ruta in ("caja:resumen", "menu:plato_lista", "usuarios:lista", "usuarios:registro"):
            self.assertNotIn(reverse(ruta), portada)

    def test_mesero_ve_su_trabajo_pero_no_usuarios(self):
        portada = self.enlaces(sesion(Rol.MESERO))
        for ruta in ("pedidos:lista", "reservas:lista", "menu:plato_lista", "caja:resumen"):
            self.assertIn(reverse(ruta), portada)
        self.assertNotIn(reverse("usuarios:lista"), portada)

    def test_administrador_ve_ademas_usuarios(self):
        portada = self.enlaces(sesion(Rol.ADMINISTRADOR))
        for ruta in ("pedidos:lista", "reservas:lista", "menu:plato_lista", "caja:resumen", "usuarios:lista"):
            self.assertIn(reverse(ruta), portada)


class PlatosDestacadosTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.fuertes = Categoria.objects.create(nombre="Fuertes", orden=1)
        self.oculta = Categoria.objects.create(nombre="Oculta", orden=2, activa=False)

    def plato(self, nombre, **extra):
        return Plato.objects.create(categoria=extra.pop("categoria", self.fuertes), nombre=nombre, precio="10000", **extra)

    def mostrados(self):
        return [p.nombre for p in self.client.get(reverse("inicio")).context["destacados"]]

    def test_muestra_solo_los_marcados_como_destacados(self):
        self.plato("Estrella", destacado=True)
        self.plato("Normal")
        self.assertEqual(self.mostrados(), ["Estrella"])

    def test_nunca_muestra_platos_agotados_ni_de_categorias_ocultas(self):
        self.plato("Visible", destacado=True)
        self.plato("Agotado", destacado=True, disponible=False)
        self.plato("Escondido", destacado=True, categoria=self.oculta)
        self.assertEqual(self.mostrados(), ["Visible"])

    def test_sin_destacados_muestra_los_primeros_con_foto_primero(self):
        self.plato("Sin foto")
        con_foto = self.plato("Con foto")
        con_foto.imagen = subida()
        con_foto.save()
        self.assertEqual(self.mostrados(), ["Con foto", "Sin foto"])

    def test_maximo_seis_platos(self):
        for numero in range(9):
            self.plato(f"Plato {numero}", destacado=True)
        self.assertEqual(len(self.mostrados()), 6)

    def test_sin_platos_no_muestra_la_seccion(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, "Platos destacados")

    def test_muestra_la_foto_o_un_marcador_con_la_inicial(self):
        con_foto = self.plato("Asado", destacado=True)
        con_foto.imagen = subida()
        con_foto.save()
        self.plato("Brownie", destacado=True)
        pagina = self.client.get(reverse("inicio")).content.decode()
        self.assertIn(f'<img class="foto-plato" src="{con_foto.imagen.url}"', pagina)
        self.assertIn("foto-plato--vacia", pagina)
        self.assertIn("<span>B</span>", pagina)

    def test_los_textos_se_muestran_escapados(self):
        self.plato("Seguro", destacado=True, descripcion="Rico & sano")
        self.assertContains(self.client.get(reverse("inicio")), "Rico &amp; sano")
