from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Rol, Usuario

CLAVE = "Contr4seña-Muy-Segura!"


def crear(email, rol, **extra):
    return Usuario.objects.create_user(email, CLAVE, first_name="Nombre", last_name="Apellido", rol=rol, **extra)


class RegistroYLoginTests(TestCase):
    def test_registro_crea_cliente_e_inicia_sesion(self):
        respuesta = self.client.post(reverse("usuarios:registro"), {
            "first_name": "Ana", "last_name": "Gómez", "email": "ana@ejemplo.com", "telefono": "",
            "password1": CLAVE, "password2": CLAVE, "rol": Rol.ADMINISTRADOR,
        })
        self.assertRedirects(respuesta, reverse("inicio"))
        usuario = Usuario.objects.get(email="ana@ejemplo.com")
        self.assertEqual(usuario.rol, Rol.CLIENTE)
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_registro_invalido_no_crea_usuario(self):
        respuesta = self.client.post(reverse("usuarios:registro"), {
            "first_name": "Ana1", "last_name": "Gómez", "email": "no-es-correo", "password1": "a", "password2": "b",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_login_correcto_e_incorrecto(self):
        crear("cli@ejemplo.com", Rol.CLIENTE)
        malo = self.client.post(reverse("usuarios:login"), {"username": "cli@ejemplo.com", "password": "mala"})
        self.assertEqual(malo.status_code, 200)
        bueno = self.client.post(reverse("usuarios:login"), {"username": "CLI@ejemplo.com", "password": CLAVE})
        self.assertRedirects(bueno, reverse("inicio"))

    def test_login_con_inyeccion_sql_no_entra_ni_falla(self):
        crear("cli@ejemplo.com", Rol.CLIENTE)
        respuesta = self.client.post(reverse("usuarios:login"), {"username": "' OR '1'='1' --", "password": "' OR '1'='1"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_solo_por_post(self):
        crear("cli@ejemplo.com", Rol.CLIENTE)
        self.client.login(username="cli@ejemplo.com", password=CLAVE)
        self.assertEqual(self.client.get(reverse("usuarios:logout")).status_code, 405)
        self.client.post(reverse("usuarios:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)


class ControlDeAccesoTests(TestCase):
    def setUp(self):
        self.cliente = crear("cli@ejemplo.com", Rol.CLIENTE)
        self.mesero = crear("mes@ejemplo.com", Rol.MESERO)
        self.admin = crear("adm@ejemplo.com", Rol.ADMINISTRADOR)

    def ir(self, usuario, nombre):
        self.client.logout()
        if usuario:
            self.client.force_login(usuario)
        return self.client.get(reverse(nombre))

    def test_visitante_es_redirigido_al_login(self):
        for nombre in ("usuarios:lista", "usuarios:personal_nuevo", "usuarios:perfil"):
            r = self.ir(None, nombre)
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("usuarios:login"), r.url)

    def test_solo_el_administrador_ve_el_listado_y_crea_personal(self):
        for nombre in ("usuarios:lista", "usuarios:personal_nuevo"):
            self.assertEqual(self.ir(self.cliente, nombre).status_code, 403)
            self.assertEqual(self.ir(self.mesero, nombre).status_code, 403)
            self.assertEqual(self.ir(self.admin, nombre).status_code, 200)

    def test_cualquier_usuario_con_sesion_ve_su_perfil(self):
        for usuario in (self.cliente, self.mesero, self.admin):
            self.assertEqual(self.ir(usuario, "usuarios:perfil").status_code, 200)

    def test_cliente_no_puede_crear_personal_por_post(self):
        self.client.force_login(self.cliente)
        r = self.client.post(reverse("usuarios:personal_nuevo"), {
            "first_name": "Eve", "last_name": "Hacker", "email": "eve@ejemplo.com",
            "password1": CLAVE, "password2": CLAVE, "rol": Rol.ADMINISTRADOR,
        })
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Usuario.objects.filter(email="eve@ejemplo.com").exists())


class AdministracionTests(TestCase):
    def setUp(self):
        self.admin = crear("adm@ejemplo.com", Rol.ADMINISTRADOR)
        crear("lucia@ejemplo.com", Rol.CLIENTE)
        self.client.force_login(self.admin)

    def test_admin_crea_mesero(self):
        r = self.client.post(reverse("usuarios:personal_nuevo"), {
            "first_name": "Mario", "last_name": "Mesa", "email": "mario@ejemplo.com", "telefono": "3001234567",
            "password1": CLAVE, "password2": CLAVE, "rol": Rol.MESERO,
        })
        self.assertRedirects(r, reverse("usuarios:lista"))
        self.assertEqual(Usuario.objects.get(email="mario@ejemplo.com").rol, Rol.MESERO)

    def test_busqueda_filtra_por_texto_y_rol(self):
        r = self.client.get(reverse("usuarios:lista"), {"q": "lucia", "rol": Rol.CLIENTE})
        self.assertEqual([u.email for u in r.context["usuarios"]], ["lucia@ejemplo.com"])
        r = self.client.get(reverse("usuarios:lista"), {"q": "lucia", "rol": Rol.MESERO})
        self.assertEqual(len(r.context["usuarios"]), 0)

    def test_busqueda_con_inyeccion_devuelve_vacio_sin_error_y_conserva_la_tabla(self):
        for q in ["' OR 1=1 --", "x'; DROP TABLE usuarios_usuario; --", "<script>alert(1)</script>"]:
            with self.subTest(q=q):
                r = self.client.get(reverse("usuarios:lista"), {"q": q})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(len(r.context["usuarios"]), 0)
                self.assertTrue(r.context["formulario"].errors)
        self.assertEqual(Usuario.objects.count(), 2)

    def test_perfil_actualiza_solo_campos_permitidos(self):
        r = self.client.post(reverse("usuarios:perfil"), {
            "first_name": "Nuevo", "last_name": "Nombre", "telefono": "300 111 2222",
            "email": "otro@ejemplo.com", "rol": Rol.CLIENTE,
        })
        self.assertRedirects(r, reverse("usuarios:perfil"))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, "Nuevo")
        self.assertEqual(self.admin.telefono, "3001112222")
        self.assertEqual(self.admin.email, "adm@ejemplo.com")
        self.assertEqual(self.admin.rol, Rol.ADMINISTRADOR)
