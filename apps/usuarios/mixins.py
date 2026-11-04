"""Mixins de permisos por rol. Toda vista protegida del proyecto debe usar uno de ellos.

- Visitante sin sesión: se redirige al inicio de sesión.
- Usuario con sesión pero sin el rol requerido: respuesta 403.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Rol


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    roles_permitidos = ()

    def test_func(self):
        usuario = self.request.user
        return usuario.is_authenticated and usuario.is_active and usuario.rol in self.roles_permitidos


class ClienteRequeridoMixin(RolRequeridoMixin):
    roles_permitidos = (Rol.CLIENTE,)


class PersonalRequeridoMixin(RolRequeridoMixin):
    """Personal del restaurante: meseros y administradores."""

    roles_permitidos = (Rol.MESERO, Rol.ADMINISTRADOR)


class AdministradorRequeridoMixin(RolRequeridoMixin):
    roles_permitidos = (Rol.ADMINISTRADOR,)
