from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from apps.caja.services import caja_cerrada, emitir_factura
from apps.comun.views import FiltrosEnPaginacionMixin
from apps.usuarios.mixins import PersonalRequeridoMixin

from .forms import CambioEstadoForm, FiltroPedidoForm, PedidoForm
from .models import Estado, Pedido, SIGUIENTE
from .services import crear_pedido


class PedidosVisiblesMixin(LoginRequiredMixin):
    """El personal ve todos los pedidos; un cliente solo los suyos (los ajenos responden 404)."""

    def get_queryset(self):
        consulta = Pedido.objects.select_related("cliente", "creado_por").prefetch_related("items__plato")
        usuario = self.request.user
        if usuario.es_personal:
            return consulta
        return consulta.filter(cliente=usuario)

    def es_parcial(self):
        return self.request.GET.get("parcial") == "1"


class PedidoCreateView(LoginRequiredMixin, FormView):
    form_class = PedidoForm
    template_name = "pedidos/formulario.html"
    extra_context = {"seccion": "pedido_nuevo"}

    def form_valid(self, form):
        pedido = crear_pedido(self.request.user, form.cleaned_data["mesa"], form.cleaned_data["notas"], form.items)
        messages.success(self.request, f"Pedido #{pedido.pk} registrado.")
        return redirect("pedidos:detalle", pk=pedido.pk)


class PedidoListView(PedidosVisiblesMixin, FiltrosEnPaginacionMixin, ListView):
    context_object_name = "pedidos"
    paginate_by = 20
    extra_context = {"seccion": "pedidos"}

    def get_template_names(self):
        return ["pedidos/_tabla.html"] if self.es_parcial() else ["pedidos/lista.html"]

    def get_formulario(self):
        if not hasattr(self, "_formulario"):
            filtros = {k: v for k, v in self.request.GET.items() if k in FiltroPedidoForm.base_fields}
            self._formulario = FiltroPedidoForm(filtros or None)
        return self._formulario

    def get_queryset(self):
        consulta = super().get_queryset()
        formulario = self.get_formulario()
        if not formulario.is_bound:
            return consulta
        if not formulario.is_valid():
            return consulta.none()
        estado, mesa = formulario.cleaned_data["estado"], formulario.cleaned_data["mesa"]
        if estado == "activos":
            consulta = consulta.filter(estado__in=list(SIGUIENTE))
        elif estado:
            consulta = consulta.filter(estado=estado)
        if mesa:
            consulta = consulta.filter(mesa=mesa)
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario"] = self.get_formulario()
        return contexto


class PedidoDetailView(PedidosVisiblesMixin, DetailView):
    context_object_name = "pedido"
    extra_context = {"seccion": "pedidos"}

    def get_template_names(self):
        return ["pedidos/_estado.html"] if self.es_parcial() else ["pedidos/detalle.html"]


class PedidoAvanzarView(PersonalRequeridoMixin, View):
    """El personal avanza el pedido al siguiente estado del flujo."""

    http_method_names = ["post"]

    def post(self, request, pk):
        formulario = CambioEstadoForm(request.POST)
        with transaction.atomic():
            pedido = get_object_or_404(Pedido.objects.select_for_update(), pk=pk)
            if not formulario.is_valid() or formulario.cleaned_data["desde"] != pedido.estado:
                messages.error(request, "El estado del pedido cambió mientras lo veías. Revísalo e inténtalo de nuevo.")
            elif pedido.siguiente_estado is None:
                messages.error(request, "El pedido ya está en su estado final.")
            elif pedido.siguiente_estado == Estado.CERRADO and caja_cerrada(timezone.localdate()):
                messages.error(request, "La caja de hoy ya está cerrada: no se pueden cerrar más pedidos hoy.")
            else:
                pedido.avanzar()
                messages.success(request, f"Pedido #{pedido.pk}: {Estado(pedido.estado).label}.")
                if pedido.estado == Estado.CERRADO:
                    factura = emitir_factura(pedido, request.user)
                    messages.success(request, f"Factura {factura.numero} emitida por $ {factura.total}.")
        return redirect("pedidos:detalle", pk=pk)


class PedidoCancelarView(PedidosVisiblesMixin, View):
    """Cancela un pedido pendiente: el personal cualquiera; el cliente, solo el suyo."""

    http_method_names = ["post"]

    def post(self, request, pk):
        with transaction.atomic():
            pedido = get_object_or_404(self.get_queryset().select_for_update(of=("self",)), pk=pk)
            if pedido.puede_cancelarse:
                pedido.cancelar()
                messages.success(request, f"Pedido #{pedido.pk} cancelado.")
            else:
                messages.error(request, "Solo se puede cancelar un pedido que sigue pendiente.")
        return redirect(reverse("pedidos:detalle", args=[pk]))
