from django.urls import path

from . import views

app_name = "caja"

urlpatterns = [
    path("", views.ResumenCajaView.as_view(), name="resumen"),
    path("cierre/nuevo/", views.CierreCajaCreateView.as_view(), name="cierre_nuevo"),
    path("cierres/", views.CierreCajaListView.as_view(), name="cierres"),
    path("reportes/", views.ReporteVentasView.as_view(), name="reportes"),
    path("facturas/", views.FacturaListView.as_view(), name="facturas"),
    path("facturas/<int:pk>/", views.FacturaDetailView.as_view(), name="factura"),
]
