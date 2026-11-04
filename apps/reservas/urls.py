from django.urls import path

from . import views

app_name = "reservas"

urlpatterns = [
    path("", views.ReservaListView.as_view(), name="lista"),
    path("nueva/", views.ReservaCreateView.as_view(), name="nueva"),
    path("<int:pk>/confirmar/", views.ReservaTransicionView.as_view(accion="confirmar", etiqueta="confirmada"), name="confirmar"),
    path("<int:pk>/completar/", views.ReservaTransicionView.as_view(accion="completar", etiqueta="completada"), name="completar"),
    path("<int:pk>/cancelar/", views.ReservaCancelarView.as_view(), name="cancelar"),
]
