from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.PedidoListView.as_view(), name="lista"),
    path("nuevo/", views.PedidoCreateView.as_view(), name="nuevo"),
    path("<int:pk>/", views.PedidoDetailView.as_view(), name="detalle"),
    path("<int:pk>/avanzar/", views.PedidoAvanzarView.as_view(), name="avanzar"),
    path("<int:pk>/cancelar/", views.PedidoCancelarView.as_view(), name="cancelar"),
]
