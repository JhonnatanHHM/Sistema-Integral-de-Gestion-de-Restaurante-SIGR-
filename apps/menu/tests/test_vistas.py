from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.menu.models import Categoria, Plato
from apps.usuarios.models import Rol, Usuario

CLAVE = "Contr4seña-Muy-Segura!"


def crear(email, rol):
    return Usuario.objects.create_user(email, CLAVE, first_name="Nombre", last_name="Apellido", rol=rol)


class DatosMenuMixin:
    def setUp(self):
        self.cliente = crear("cli@ejemplo.com", Rol.CLIENTE)
        self.mesero = crear("mes@ejemplo.com", Rol.MESERO)
        self.admin = crear("adm@ejemplo.com", Rol.ADMINISTRADOR)
        self.fuertes = Categoria.objects.create(nombre="Fuertes", orden=1)
        self.postres = Categoria.objects.create(nombre="Postres", orden=2)
        self.oculta = Categoria.objects.create(nombre="Oculta", orden=3, activa=False)
        self.pasta = Plato.objects.create(categoria=self.fuertes, nombre="Pasta alfredo", precio="28000")
        self.agotado = Plato.objects.create(categoria=self.fuertes, nombre="Salmón", precio="42500", disponible=False)
        self.brownie = Plato.objects.create(categoria=self.postres, nombre="Brownie", precio="14500")
        self.secreto = Plato.objects.create(categoria=self.oculta, nombre="Plato secreto", precio="1000")


class MenuPublicoTests(DatosMenuMixin, TestCase):
    def test_visitante_ve_solo_disponibles_de_categorias_activas(self):
        r = self.client.get(reverse("menu:publico"))
        self.assertEqual(r.status_code, 200)
        nombres = [p.nombre for _, platos in r.context["grupos"] for p in platos]
        self.assertEqual(nombres, ["Pasta alfredo", "Brownie"])

    def test_busqueda_y_filtro_por_categoria(self):
        r = self.client.get(reverse("menu:publico"), {"q": "brown"})
        self.assertEqual([p.nombre for _, ps in r.context["grupos"] for p in ps], ["Brownie"])
        r = self.client.get(reverse("menu:publico"), {"categoria": self.fuertes.pk})
        self.assertEqual([p.nombre for _, ps in r.context["grupos"] for p in ps], ["Pasta alfredo"])

    def test_inyeccion_en_busqueda_no_falla_ni_filtra_datos(self):
        for params in [{"q": "' OR 1=1 --"}, {"q": "x'; DROP TABLE menu_plato; --"}, {"categoria": "1 OR 1=1"}, {"categoria": "999"}]:
            with self.subTest(params=params):
                r = self.client.get(reverse("menu:publico"), params)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.context["grupos"], [])
        self.assertEqual(Plato.objects.count(), 4)

    def test_no_muestra_html_inyectado(self):
        Plato.objects.create(categoria=self.postres, nombre="Flan", descripcion="rico", precio="5000")
        r = self.client.get(reverse("menu:publico"))
        self.assertNotContains(r, "<script>")


class ControlDeAccesoTests(DatosMenuMixin, TestCase):
    def ir(self, usuario, nombre, *args, metodo="get"):
        self.client.logout()
        if usuario:
            self.client.force_login(usuario)
        return getattr(self.client, metodo)(reverse(nombre, args=args))

    def test_visitante_redirigido_al_login(self):
        for nombre, args in [("menu:plato_lista", ()), ("menu:plato_nuevo", ()), ("menu:categoria_lista", ()), ("menu:plato_editar", (self.pasta.pk,))]:
            r = self.ir(None, nombre, *args)
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("usuarios:login"), r.url)

    def test_cliente_no_accede_a_la_gestion(self):
        for nombre, args in [("menu:plato_lista", ()), ("menu:plato_nuevo", ()), ("menu:categoria_lista", ()), ("menu:plato_eliminar", (self.pasta.pk,))]:
            self.assertEqual(self.ir(self.cliente, nombre, *args).status_code, 403, nombre)

    def test_mesero_ve_platos_pero_no_crea_ni_edita_ni_gestiona_categorias(self):
        self.assertEqual(self.ir(self.mesero, "menu:plato_lista").status_code, 200)
        for nombre, args in [("menu:plato_nuevo", ()), ("menu:plato_editar", (self.pasta.pk,)), ("menu:plato_eliminar", (self.pasta.pk,)), ("menu:categoria_lista", ()), ("menu:categoria_nueva", ())]:
            self.assertEqual(self.ir(self.mesero, nombre, *args).status_code, 403, nombre)

    def test_mesero_puede_marcar_disponibilidad_cliente_no(self):
        self.assertEqual(self.ir(self.cliente, "menu:plato_disponibilidad", self.pasta.pk, metodo="post").status_code, 403)
        self.ir(self.mesero, "menu:plato_disponibilidad", self.pasta.pk, metodo="post")
        self.pasta.refresh_from_db()
        self.assertFalse(self.pasta.disponible)

    def test_disponibilidad_no_acepta_get(self):
        self.assertEqual(self.ir(self.admin, "menu:plato_disponibilidad", self.pasta.pk).status_code, 405)

    def test_gestion_lista_busqueda_con_inyeccion(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("menu:plato_lista"), {"q": "' OR 1=1 --"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["platos"]), 0)
        r = self.client.get(reverse("menu:plato_lista"), {"disponible": "0"})
        nombres = [p.nombre for p in r.context["platos"]]
        self.assertIn("Salmón", nombres)
        self.assertNotIn("Pasta alfredo", nombres)


class CrudAdministradorTests(DatosMenuMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_crear_plato(self):
        r = self.client.post(reverse("menu:plato_nuevo"), {"categoria": self.postres.pk, "nombre": "Flan", "descripcion": "De caramelo", "precio": "8000", "disponible": "on"})
        self.assertRedirects(r, reverse("menu:plato_lista"))
        self.assertEqual(Plato.objects.get(nombre="Flan").precio, 8000)

    def test_crear_plato_invalido_no_guarda(self):
        r = self.client.post(reverse("menu:plato_nuevo"), {"categoria": self.postres.pk, "nombre": "Flan", "precio": "gratis"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Plato.objects.filter(nombre="Flan").exists())

    def test_editar_y_eliminar_plato(self):
        r = self.client.post(reverse("menu:plato_editar", args=[self.pasta.pk]), {"categoria": self.fuertes.pk, "nombre": "Pasta boloñesa", "descripcion": "", "precio": "30000", "disponible": "on"})
        self.assertRedirects(r, reverse("menu:plato_lista"))
        self.pasta.refresh_from_db()
        self.assertEqual((self.pasta.nombre, self.pasta.precio), ("Pasta boloñesa", 30000))
        self.client.post(reverse("menu:plato_eliminar", args=[self.pasta.pk]))
        self.assertFalse(Plato.objects.filter(pk=self.pasta.pk).exists())

    def test_crud_categoria(self):
        self.client.post(reverse("menu:categoria_nueva"), {"nombre": "Bebidas", "descripcion": "", "orden": "5", "activa": "on"})
        bebidas = Categoria.objects.get(nombre="Bebidas")
        self.client.post(reverse("menu:categoria_editar", args=[bebidas.pk]), {"nombre": "Bebidas frías", "descripcion": "", "orden": "5", "activa": "on"})
        bebidas.refresh_from_db()
        self.assertEqual(bebidas.nombre, "Bebidas frías")
        self.client.post(reverse("menu:categoria_eliminar", args=[bebidas.pk]))
        self.assertFalse(Categoria.objects.filter(pk=bebidas.pk).exists())

    def test_no_se_elimina_categoria_con_platos(self):
        r = self.client.post(reverse("menu:categoria_eliminar", args=[self.fuertes.pk]), follow=True)
        self.assertTrue(Categoria.objects.filter(pk=self.fuertes.pk).exists())
        self.assertContains(r, "No se puede eliminar")


class CargarMenuDemoTests(TestCase):
    def test_es_idempotente(self):
        call_command("cargar_menu_demo", verbosity=0)
        total = Plato.objects.count()
        call_command("cargar_menu_demo", verbosity=0)
        self.assertEqual(Plato.objects.count(), total)
        self.assertGreater(total, 0)
