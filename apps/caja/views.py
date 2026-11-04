from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from apps.comun.views import FiltrosEnPaginacionMixin
from apps.usuarios.mixins import AdministradorRequeridoMixin, PersonalRequeridoMixin

from .forms import FORMATO_FECHA, CierreCajaForm, RangoFechasForm
from .models import CierreCaja, Factura
from .services import (
    cerrar_caja, pedidos_activos_del_dia, platos_mas_vendidos, totales_del_rango, ventas_del_dia, ventas_por_dia,
)


class ResumenCajaView(PersonalRequeridoMixin, TemplateView):
    """Panel del día. El mesero solo ve el total; el administrador ve además los accesos de gestión."""

    template_name = "caja/resumen.html"
    extra_context = {"seccion": "caja"}

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        total, cantidad = ventas_del_dia(hoy)
        contexto.update(
            hoy=hoy, total=total, facturas=cantidad,
            cierre=CierreCaja.objects.filter(fecha=hoy).first(),
            pedidos_activos=pedidos_activos_del_dia(hoy),
        )
        return contexto


class CierreCajaCreateView(AdministradorRequeridoMixin, CreateView):
    form_class = CierreCajaForm
    template_name = "caja/cierre_form.html"
    success_url = reverse_lazy("caja:cierres")
    extra_context = {"seccion": "caja"}

    def get_initial(self):
        return {"fecha": timezone.localdate()}

    def form_valid(self, form):
        datos = form.cleaned_data
        try:
            cierre = cerrar_caja(datos["fecha"], datos["efectivo_contado"], datos["observaciones"], self.request.user)
        except IntegrityError:
            form.add_error("fecha", "La caja de esta fecha ya fue cerrada.")
            return self.form_invalid(form)
        self.object = cierre
        messages.success(self.request, f"Caja del {cierre.fecha:%d/%m/%Y} cerrada: {cierre.resultado.lower()}.")
        return redirect(self.success_url)


class CierreCajaListView(AdministradorRequeridoMixin, ListView):
    model = CierreCaja
    template_name = "caja/cierre_lista.html"
    context_object_name = "cierres"
    paginate_by = 31
    extra_context = {"seccion": "caja"}


class ReporteVentasView(AdministradorRequeridoMixin, TemplateView):
    template_name = "caja/reporte.html"
    extra_context = {"seccion": "caja"}

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        datos = {
            "desde": self.request.GET.get("desde") or (hoy - timedelta(days=6)).strftime(FORMATO_FECHA),
            "hasta": self.request.GET.get("hasta") or hoy.strftime(FORMATO_FECHA),
        }
        formulario = RangoFechasForm(datos)
        contexto["formulario"] = formulario
        if formulario.is_valid():
            desde, hasta = formulario.cleaned_data["desde"], formulario.cleaned_data["hasta"]
            total, facturas = totales_del_rango(desde, hasta)
            contexto.update(
                dias=ventas_por_dia(desde, hasta), platos=platos_mas_vendidos(desde, hasta),
                total=total, facturas=facturas, desde=desde, hasta=hasta,
                ticket_promedio=(total / facturas) if facturas else 0,
            )
        return contexto


class FacturaListView(AdministradorRequeridoMixin, FiltrosEnPaginacionMixin, ListView):
    template_name = "caja/factura_lista.html"
    context_object_name = "facturas"
    paginate_by = 25
    extra_context = {"seccion": "caja"}

    def get_queryset(self):
        return Factura.objects.select_related("pedido", "emitida_por")


class FacturaDetailView(LoginRequiredMixin, DetailView):
    """El personal ve cualquier factura; un cliente solo la de sus pedidos (las ajenas responden 404)."""

    template_name = "caja/factura_detalle.html"
    context_object_name = "factura"
    extra_context = {"seccion": "pedidos"}

    def get_queryset(self):
        consulta = Factura.objects.select_related("pedido", "pedido__cliente", "pedido__creado_por", "emitida_por")
        usuario = self.request.user
        return consulta if usuario.es_personal else consulta.filter(pedido__cliente=usuario)
