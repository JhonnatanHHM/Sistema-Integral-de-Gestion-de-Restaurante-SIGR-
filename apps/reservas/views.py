from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from apps.comun.views import FiltrosEnPaginacionMixin
from apps.usuarios.mixins import ClienteRequeridoMixin, PersonalRequeridoMixin

from .forms import CambioEstadoReservaForm, FiltroReservaForm, ReservaForm
from .models import VIGENTES, EstadoReserva, Reserva
from .services import ReservaNoDisponible, crear_reserva


class ReservasVisiblesMixin(LoginRequiredMixin):
    """El personal ve todas las reservas; un cliente solo las suyas (las ajenas responden 404)."""

    def get_queryset(self):
        consulta = Reserva.objects.select_related("cliente")
        usuario = self.request.user
        return consulta if usuario.es_personal else consulta.filter(cliente=usuario)


class ReservaCreateView(ClienteRequeridoMixin, CreateView):
    form_class = ReservaForm
    template_name = "reservas/formulario.html"
    success_url = reverse_lazy("reservas:lista")
    extra_context = {"seccion": "reservas"}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["cliente"] = self.request.user
        return kwargs

    def form_valid(self, form):
        reserva = form.save(commit=False)
        reserva.cliente = self.request.user
        try:
            crear_reserva(reserva)
        except ReservaNoDisponible as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        self.object = reserva
        messages.success(self.request, "Reserva registrada. Quedó pendiente de confirmación.")
        return redirect(self.success_url)


class ReservaListView(ReservasVisiblesMixin, FiltrosEnPaginacionMixin, ListView):
    context_object_name = "reservas"
    paginate_by = 20
    extra_context = {"seccion": "reservas"}

    def get_template_names(self):
        return ["reservas/_tabla.html"] if self.request.GET.get("parcial") == "1" else ["reservas/lista.html"]

    def get_formulario(self):
        if not hasattr(self, "_formulario"):
            filtros = {k: v for k, v in self.request.GET.items() if k in FiltroReservaForm.base_fields}
            self._formulario = FiltroReservaForm(filtros or None)
        return self._formulario

    def get_queryset(self):
        consulta = super().get_queryset()
        formulario = self.get_formulario()
        if not formulario.is_bound:
            return consulta
        if not formulario.is_valid():
            return consulta.none()
        datos = formulario.cleaned_data
        if datos["estado"] == "vigentes":
            consulta = consulta.filter(estado__in=VIGENTES)
        elif datos["estado"]:
            consulta = consulta.filter(estado=datos["estado"])
        if datos["fecha"]:
            consulta = consulta.filter(fecha=datos["fecha"])
        if datos["mesa"]:
            consulta = consulta.filter(mesa=datos["mesa"])
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario"] = self.get_formulario()
        return contexto


def _cambiar_estado(request, consulta, pk, accion, etiqueta):
    """Aplica `accion` ('confirmar', 'completar', 'cancelar') si la pantalla seguía actualizada."""
    formulario = CambioEstadoReservaForm(request.POST)
    with transaction.atomic():
        reserva = get_object_or_404(consulta.select_for_update(of=("self",)), pk=pk)
        if not formulario.is_valid() or formulario.cleaned_data["desde"] != reserva.estado:
            messages.error(request, "La reserva cambió mientras la veías. Revísala e inténtalo de nuevo.")
            return
        try:
            getattr(reserva, accion)()
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Reserva #{reserva.pk} {etiqueta}.")


class ReservaTransicionView(PersonalRequeridoMixin, View):
    """El personal confirma o completa una reserva (la acción llega por la URL)."""

    http_method_names = ["post"]
    accion = None
    etiqueta = ""

    def post(self, request, pk):
        _cambiar_estado(request, Reserva.objects.all(), pk, self.accion, self.etiqueta)
        return redirect("reservas:lista")


class ReservaCancelarView(ReservasVisiblesMixin, View):
    """Cancela una reserva vigente: el personal cualquiera; el cliente, solo la suya."""

    http_method_names = ["post"]

    def post(self, request, pk):
        _cambiar_estado(request, self.get_queryset(), pk, "cancelar", "cancelada")
        return redirect("reservas:lista")
