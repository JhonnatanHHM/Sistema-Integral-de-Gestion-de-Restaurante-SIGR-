from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("", views.MenuPublicoView.as_view(), name="publico"),
    path("gestion/platos/", views.PlatoGestionListView.as_view(), name="plato_lista"),
    path("gestion/platos/nuevo/", views.PlatoCreateView.as_view(), name="plato_nuevo"),
    path("gestion/platos/<int:pk>/editar/", views.PlatoUpdateView.as_view(), name="plato_editar"),
    path("gestion/platos/<int:pk>/eliminar/", views.PlatoDeleteView.as_view(), name="plato_eliminar"),
    path("gestion/platos/<int:pk>/disponibilidad/", views.PlatoDisponibilidadView.as_view(), name="plato_disponibilidad"),
    path("gestion/categorias/", views.CategoriaListView.as_view(), name="categoria_lista"),
    path("gestion/categorias/nueva/", views.CategoriaCreateView.as_view(), name="categoria_nueva"),
    path("gestion/categorias/<int:pk>/editar/", views.CategoriaUpdateView.as_view(), name="categoria_editar"),
    path("gestion/categorias/<int:pk>/eliminar/", views.CategoriaDeleteView.as_view(), name="categoria_eliminar"),
]
