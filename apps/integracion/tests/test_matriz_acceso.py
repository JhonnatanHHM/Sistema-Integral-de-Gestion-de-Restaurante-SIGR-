"""Matriz de permisos: qué rol puede abrir cada pantalla. Si se agrega una ruta nueva sin declararla aquí, falla."""
from django.test import Client, TestCase
from django.urls import get_resolver, reverse

from apps.usuarios.models import Rol

from .base import EntornoMixin

VISITANTE = "visitante"
TODOS = {VISITANTE, Rol.CLIENTE, Rol.MESERO, Rol.ADMINISTRADOR}
CON_SESION = {Rol.CLIENTE, Rol.MESERO, Rol.ADMINISTRADOR}
PERSONAL = {Rol.MESERO, Rol.ADMINISTRADOR}
SOLO_ADMIN = {Rol.ADMINISTRADOR}
SOLO_CLIENTE = {Rol.CLIENTE}

# Rutas sin parámetros: nombre -> roles que pueden abrirlas (GET).
RUTAS = {
    "inicio": TODOS,
    "menu:publico": TODOS,
    "usuarios:login": {VISITANTE},            # con sesión iniciada redirige al inicio
    "usuarios:registro": {VISITANTE},
    "usuarios:perfil": CON_SESION,
    "usuarios:lista": SOLO_ADMIN,
    "usuarios:personal_nuevo": SOLO_ADMIN,
    "menu:plato_lista": PERSONAL,
    "menu:plato_nuevo": SOLO_ADMIN,
    "menu:categoria_lista": SOLO_ADMIN,
    "menu:categoria_nueva": SOLO_ADMIN,
    "pedidos:lista": CON_SESION,
    "pedidos:nuevo": CON_SESION,
    "reservas:lista": CON_SESION,
    "reservas:nueva": SOLO_CLIENTE,
    "caja:resumen": PERSONAL,
    "caja:cierre_nuevo": SOLO_ADMIN,
    "caja:cierres": SOLO_ADMIN,
    "caja:reportes": SOLO_ADMIN,
    "caja:facturas": SOLO_ADMIN,
}

# Rutas con parámetro (pk): nombre -> roles autorizados. Se prueban con un pk inexistente:
# el permiso se evalúa antes de buscar el objeto, así que solo importa quién puede intentarlo.
RUTAS_CON_PK = {
    "menu:plato_editar": SOLO_ADMIN,
    "menu:plato_eliminar": SOLO_ADMIN,
    "menu:plato_disponibilidad": PERSONAL,
    "menu:categoria_editar": SOLO_ADMIN,
    "menu:categoria_eliminar": SOLO_ADMIN,
    "pedidos:detalle": CON_SESION,
    "pedidos:avanzar": PERSONAL,
    "pedidos:cancelar": CON_SESION,
    "reservas:confirmar": PERSONAL,
    "reservas:completar": PERSONAL,
    "reservas:cancelar": CON_SESION,
    "caja:factura": CON_SESION,
}
# El cierre de sesión solo acepta POST y no entra en la matriz de GET.
OMITIDAS = {"usuarios:logout"}


def nombres_de_rutas():
    """Todos los nombres de URL del proyecto, salvo el sitio de administración de Django."""
    resolutor = get_resolver()
    nombres = {n for n in resolutor.reverse_dict if isinstance(n, str)}
    for espacio, (_, sub) in resolutor.namespace_dict.items():
        if espacio != "admin":
            nombres |= {f"{espacio}:{n}" for n in sub.reverse_dict if isinstance(n, str)}
    return nombres


class MatrizDeAccesoTests(EntornoMixin, TestCase):
    def navegador(self, rol):
        navegador = Client()
        if rol != VISITANTE:
            usuario = {Rol.CLIENTE: self.cliente, Rol.MESERO: self.mesero, Rol.ADMINISTRADOR: self.admin}[rol]
            navegador.force_login(usuario)
        return navegador

    def esperado(self, rol, permitidos):
        if rol in permitidos:
            return {200}
        return {302} if rol == VISITANTE or permitidos == {VISITANTE} else {403}

    def test_toda_ruta_del_proyecto_esta_declarada_en_la_matriz(self):
        declaradas = set(RUTAS) | set(RUTAS_CON_PK) | OMITIDAS
        self.assertEqual(nombres_de_rutas() - declaradas, set(), "Hay rutas sin declarar en la matriz de acceso")
        self.assertEqual(declaradas - nombres_de_rutas(), set(), "La matriz declara rutas que ya no existen")

    def test_rutas_sin_parametros(self):
        for nombre, permitidos in RUTAS.items():
            for rol in TODOS:
                with self.subTest(ruta=nombre, rol=rol):
                    respuesta = self.navegador(rol).get(reverse(nombre))
                    if rol not in permitidos and rol != VISITANTE and permitidos == {VISITANTE}:
                        self.assertEqual(respuesta.status_code, 302)              # login/registro con sesión: al inicio
                    else:
                        self.assertIn(respuesta.status_code, self.esperado(rol, permitidos))
                    if respuesta.status_code == 302 and rol == VISITANTE and permitidos != TODOS:
                        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_rutas_con_parametro(self):
        for nombre, permitidos in RUTAS_CON_PK.items():
            for rol in TODOS:
                with self.subTest(ruta=nombre, rol=rol):
                    respuesta = self.navegador(rol).get(reverse(nombre, args=[999999]))
                    if rol in permitidos:
                        self.assertIn(respuesta.status_code, {404, 405})     # autorizado: el objeto no existe o exige POST
                    elif rol == VISITANTE:
                        self.assertEqual(respuesta.status_code, 302)
                        self.assertIn(reverse("usuarios:login"), respuesta.url)
                    else:
                        self.assertEqual(respuesta.status_code, 403)

    def test_un_usuario_desactivado_pierde_el_acceso(self):
        self.mesero.is_active = False
        self.mesero.save()
        navegador = Client()
        navegador.force_login(self.mesero)
        respuesta = navegador.get(reverse("caja:resumen"))
        self.assertEqual(respuesta.status_code, 302)
