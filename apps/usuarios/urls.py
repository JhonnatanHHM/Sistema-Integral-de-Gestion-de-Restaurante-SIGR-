from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("ingresar/", views.AccesoView.as_view(), name="login"),
    path("salir/", LogoutView.as_view(), name="logout"),
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("perfil/", views.PerfilView.as_view(), name="perfil"),
    path("usuarios/", views.UsuarioListView.as_view(), name="lista"),
    path("usuarios/nuevo/", views.PersonalCreateView.as_view(), name="personal_nuevo"),
]
