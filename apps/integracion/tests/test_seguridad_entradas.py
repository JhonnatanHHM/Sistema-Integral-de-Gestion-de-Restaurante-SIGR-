"""Barrido de seguridad: entradas hostiles en todos los buscadores y formularios.

Regla general: ninguna carga puede provocar un error del servidor (500).
- Campos estrictos (correo, números, fechas, horas, elecciones): la carga se rechaza y no se guarda nada.
- Campos de texto libre (notas, nombres de platos): una carga puede ser texto válido y guardarse, pero siempre
  viaja como parámetro (nunca como SQL) y se muestra escapada, así que no ejecuta nada.
"""
import sass
from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from apps.caja.models import CierreCaja, Factura
from apps.menu.models import Categoria, Plato
from apps.pedidos.models import Pedido
from apps.reservas.models import Reserva
from apps.usuarios.models import Usuario

from .base import CLAVE, EntornoMixin

CARGAS = [
    "' OR 1=1 --",
    "'; DROP TABLE usuarios_usuario; --",
    "1 UNION SELECT NULL, password FROM usuarios_usuario",
    "<script>alert(1)</script>",
    "\"><img src=x onerror=alert(1)>",
    "../../etc/passwd",
    "{{7*7}}",
    "${7*7}",
    "%00",
    "%",
    "A" * 5000,
    "-1",
    "1e999",
]

# (ruta, parámetros del buscador)
BUSCADORES = [
    ("usuarios:lista", ["q", "rol"]),
    ("menu:publico", ["q", "categoria"]),
    ("menu:plato_lista", ["q", "categoria", "disponible"]),
    ("pedidos:lista", ["estado", "mesa"]),
    ("reservas:lista", ["estado", "fecha", "mesa"]),
    ("caja:reportes", ["desde", "hasta"]),
]


def tablas_intactas(prueba):
    """Las tablas siguen existiendo y consultables (ninguna carga las borró)."""
    for modelo in (Usuario, Categoria, Plato, Pedido, Reserva, Factura, CierreCaja):
        prueba.assertGreaterEqual(modelo.objects.count(), 0)
    prueba.assertTrue(Usuario.objects.filter(email="adm@ejemplo.com").exists())


class BarridoDeBuscadoresTests(EntornoMixin, TestCase):
    def test_los_buscadores_resisten_cargas_hostiles(self):
        navegador = Client()
        navegador.force_login(self.admin)
        for ruta, parametros in BUSCADORES:
            for parametro in parametros:
                for carga in CARGAS:
                    with self.subTest(ruta=ruta, parametro=parametro, carga=carga[:25]):
                        respuesta = navegador.get(reverse(ruta), {parametro: carga})
                        self.assertEqual(respuesta.status_code, 200)
                        self.assertNotContains(respuesta, "<script>alert(1)</script>")
                        self.assertNotContains(respuesta, '"><img src=x')
        tablas_intactas(self)

    def test_todos_los_parametros_juntos(self):
        navegador = Client()
        navegador.force_login(self.admin)
        for ruta, parametros in BUSCADORES:
            for carga in CARGAS:
                respuesta = navegador.get(reverse(ruta), {p: carga for p in parametros})
                self.assertEqual(respuesta.status_code, 200, (ruta, carga[:25]))
        tablas_intactas(self)

    def test_un_buscador_con_carga_invalida_devuelve_vacio_y_no_todo_el_listado(self):
        navegador = Client()
        navegador.force_login(self.admin)
        respuesta = navegador.get(reverse("usuarios:lista"), {"q": "' OR 1=1 --"})
        self.assertEqual(len(respuesta.context["usuarios"]), 0)
        respuesta = navegador.get(reverse("menu:publico"), {"q": "' OR 1=1 --"})
        self.assertEqual(respuesta.context["grupos"], [])


class BarridoDeFormulariosTests(EntornoMixin, TestCase):
    def test_el_registro_rechaza_cargas_hostiles_en_todos_sus_campos(self):
        antes = Usuario.objects.count()
        base = {"first_name": "Ana", "last_name": "Pérez", "email": "ana@ejemplo.com", "telefono": "3001234567",
                "password1": CLAVE, "password2": CLAVE}
        for carga in CARGAS:
            for campo in ("first_name", "last_name", "email", "telefono"):
                with self.subTest(campo=campo, carga=carga[:25]):
                    respuesta = Client().post(reverse("usuarios:registro"), {**base, campo: carga})
                    self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), antes)

    def test_el_login_con_cargas_hostiles_no_entra_ni_falla(self):
        for carga in CARGAS:
            navegador = Client()
            respuesta = navegador.post(reverse("usuarios:login"), {"username": carga, "password": carga})
            self.assertEqual(respuesta.status_code, 200)
            self.assertNotIn("_auth_user_id", navegador.session)

    def test_pedidos_mesa_y_cantidades_hostiles_nunca_se_guardan(self):
        navegador = Client()
        navegador.force_login(self.cliente)
        plato = Plato.objects.first()
        base = {"mesa": "4", "notas": "ok", f"plato_{plato.pk}": "1"}
        for carga in CARGAS:
            for campo in ("mesa", f"plato_{plato.pk}"):
                with self.subTest(campo=campo, carga=carga[:25]):
                    self.assertEqual(navegador.post(reverse("pedidos:nuevo"), {**base, campo: carga}).status_code, 200)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_notas_de_pedido_hostiles_no_rompen_nada_y_se_muestran_escapadas(self):
        navegador = Client()
        navegador.force_login(self.cliente)
        plato = Plato.objects.first()
        for carga in CARGAS:
            respuesta = navegador.post(reverse("pedidos:nuevo"), {"mesa": "4", "notas": carga, f"plato_{plato.pk}": "1"})
            self.assertIn(respuesta.status_code, (200, 302), carga[:25])
        for pedido in Pedido.objects.all():
            pagina = navegador.get(reverse("pedidos:detalle", args=[pedido.pk])).content.decode()
            self.assertNotIn("<script>alert(1)</script>", pagina)
        self.assertEqual(Pedido.objects.filter(notas__contains="<").count(), 0)        # ni < ni > se aceptan
        tablas_intactas(self)

    def test_reservas_con_fecha_hora_personas_o_mesa_hostiles_nunca_se_guardan(self):
        navegador = Client()
        navegador.force_login(self.cliente)
        base = {"fecha": "2026-11-12", "hora": "13:00", "personas": "2", "mesa": "3", "notas": ""}
        for carga in CARGAS:
            for campo in ("fecha", "hora", "personas", "mesa"):
                with self.subTest(campo=campo, carga=carga[:25]):
                    self.assertEqual(navegador.post(reverse("reservas:nueva"), {**base, campo: carga}).status_code, 200)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_notas_de_reserva_hostiles_no_rompen_nada(self):
        navegador = Client()
        navegador.force_login(self.cliente)
        for indice, carga in enumerate(CARGAS):
            respuesta = navegador.post(reverse("reservas:nueva"), {
                "fecha": "2026-11-%02d" % (11 + indice % 15), "hora": "13:00", "personas": "2", "mesa": "3", "notas": carga,
            })
            self.assertIn(respuesta.status_code, (200, 302), carga[:25])
        self.assertEqual(Reserva.objects.filter(notas__contains="<").count(), 0)
        tablas_intactas(self)

    def test_formularios_del_administrador_con_campos_estrictos_hostiles_nunca_guardan(self):
        navegador = Client()
        navegador.force_login(self.admin)
        categoria = Categoria.objects.first()
        casos = [
            ("menu:categoria_nueva", {"nombre": "Nueva", "descripcion": "", "orden": "1"}, "orden", Categoria),
            ("menu:plato_nuevo", {"categoria": categoria.pk, "nombre": "Nuevo", "descripcion": "", "precio": "1000"}, "precio", Plato),
            ("menu:plato_nuevo", {"categoria": categoria.pk, "nombre": "Nuevo", "descripcion": "", "precio": "1000"}, "categoria", Plato),
            ("caja:cierre_nuevo", {"fecha": "2026-11-10", "efectivo_contado": "1", "observaciones": ""}, "efectivo_contado", CierreCaja),
            ("caja:cierre_nuevo", {"fecha": "2026-11-10", "efectivo_contado": "1", "observaciones": ""}, "fecha", CierreCaja),
            ("usuarios:personal_nuevo", {"first_name": "Mario", "last_name": "Mesa", "email": "m@ejemplo.com", "telefono": "",
                                         "password1": CLAVE, "password2": CLAVE, "rol": "mesero"}, "email", Usuario),
            ("usuarios:personal_nuevo", {"first_name": "Mario", "last_name": "Mesa", "email": "m@ejemplo.com", "telefono": "",
                                         "password1": CLAVE, "password2": CLAVE, "rol": "mesero"}, "rol", Usuario),
        ]
        for ruta, base, campo, modelo in casos:
            antes = modelo.objects.count()
            for carga in CARGAS:
                with self.subTest(ruta=ruta, campo=campo, carga=carga[:25]):
                    self.assertEqual(navegador.post(reverse(ruta), {**base, campo: carga}).status_code, 200)
            self.assertEqual(modelo.objects.count(), antes, (ruta, campo))

    def test_nombres_libres_del_administrador_no_rompen_nada(self):
        navegador = Client()
        navegador.force_login(self.admin)
        for carga in CARGAS:
            for ruta, datos in [
                ("menu:categoria_nueva", {"nombre": carga, "descripcion": carga, "orden": "1"}),
                ("caja:cierre_nuevo", {"fecha": "2026-11-10", "efectivo_contado": "1", "observaciones": carga}),
            ]:
                respuesta = navegador.post(reverse(ruta), datos)
                self.assertIn(respuesta.status_code, (200, 302), (ruta, carga[:25]))
        for ruta in ("menu:categoria_lista", "menu:plato_lista", "caja:cierres"):
            pagina = navegador.get(reverse(ruta)).content.decode()
            self.assertNotIn("<script>alert(1)</script>", pagina)
        tablas_intactas(self)


class IntegridadDelProyectoTests(TestCase):
    def test_no_faltan_migraciones(self):
        # makemigrations --check termina con error (SystemExit) si un modelo cambió sin su migración.
        call_command("makemigrations", check=True, dry_run=True, verbosity=0)

    def test_la_verificacion_de_django_no_reporta_problemas(self):
        call_command("check", verbosity=0)

    def test_los_estilos_scss_compilan(self):
        css = sass.compile(filename=str(settings.BASE_DIR / "static" / "scss" / "main.scss"), output_style="compressed")
        self.assertIn(".encabezado", css)
