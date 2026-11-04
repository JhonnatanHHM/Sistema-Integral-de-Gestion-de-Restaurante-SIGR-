from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from apps.comun.views import FiltrosEnPaginacionMixin
from apps.usuarios.mixins import AdministradorRequeridoMixin, PersonalRequeridoMixin

from .forms import BusquedaMenuForm, BusquedaPlatoGestionForm, CategoriaForm, PlatoForm
from .models import Categoria, Plato


def _filtrar_platos(consulta, formulario):
    """Aplica los filtros ya validados del formulario; si hay errores devuelve una consulta vacía."""
    if not formulario.is_bound:
        return consulta
    if not formulario.is_valid():
        return consulta.none()
    datos = formulario.cleaned_data
    if datos.get("q"):
        consulta = consulta.filter(Q(nombre__icontains=datos["q"]) | Q(descripcion__icontains=datos["q"]))
    if datos.get("categoria"):
        consulta = consulta.filter(categoria=datos["categoria"])
    if datos.get("disponible") in ("0", "1"):
        consulta = consulta.filter(disponible=datos["disponible"] == "1")
    return consulta


# ---------- Menú público ----------
class MenuPublicoView(TemplateView):
    template_name = "menu/publico.html"
    extra_context = {"seccion": "menu"}

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        formulario = BusquedaMenuForm(self.request.GET or None)
        platos = Plato.objects.filter(disponible=True, categoria__activa=True).select_related("categoria")
        grupos = []
        for plato in _filtrar_platos(platos, formulario):
            if not grupos or grupos[-1][0] != plato.categoria:
                grupos.append((plato.categoria, []))
            grupos[-1][1].append(plato)
        contexto.update(formulario=formulario, grupos=grupos)
        return contexto


# ---------- Gestión de platos ----------
class PlatoGestionListView(PersonalRequeridoMixin, FiltrosEnPaginacionMixin, ListView):
    model = Plato
    template_name = "menu/plato_lista.html"
    context_object_name = "platos"
    paginate_by = 20
    extra_context = {"seccion": "gestion_menu"}

    def get_formulario(self):
        if not hasattr(self, "_formulario"):
            self._formulario = BusquedaPlatoGestionForm(self.request.GET or None)
        return self._formulario

    def get_queryset(self):
        return _filtrar_platos(Plato.objects.select_related("categoria"), self.get_formulario())

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario"] = self.get_formulario()
        return contexto


class PlatoCreateView(AdministradorRequeridoMixin, CreateView):
    model = Plato
    form_class = PlatoForm
    template_name = "menu/formulario.html"
    success_url = reverse_lazy("menu:plato_lista")
    extra_context = {"seccion": "gestion_menu", "titulo": "Nuevo plato", "volver": reverse_lazy("menu:plato_lista")}

    def form_valid(self, form):
        messages.success(self.request, "Plato creado.")
        return super().form_valid(form)


class PlatoUpdateView(AdministradorRequeridoMixin, UpdateView):
    model = Plato
    form_class = PlatoForm
    template_name = "menu/formulario.html"
    success_url = reverse_lazy("menu:plato_lista")
    extra_context = {"seccion": "gestion_menu", "titulo": "Editar plato", "volver": reverse_lazy("menu:plato_lista")}

    def form_valid(self, form):
        messages.success(self.request, "Plato actualizado.")
        return super().form_valid(form)


class PlatoDeleteView(AdministradorRequeridoMixin, DeleteView):
    model = Plato
    template_name = "menu/confirmar_eliminar.html"
    success_url = reverse_lazy("menu:plato_lista")
    extra_context = {"seccion": "gestion_menu", "volver": reverse_lazy("menu:plato_lista")}

    def form_valid(self, form):
        messages.success(self.request, "Plato eliminado.")
        return super().form_valid(form)


class PlatoDisponibilidadView(PersonalRequeridoMixin, View):
    """El personal (meseros incluidos) marca un plato como disponible o agotado."""

    http_method_names = ["post"]

    def post(self, request, pk):
        plato = get_object_or_404(Plato, pk=pk)
        plato.disponible = not plato.disponible
        plato.save(update_fields=["disponible", "actualizado"])
        estado = "disponible" if plato.disponible else "agotado"
        messages.success(request, f"«{plato.nombre}» ahora está {estado}.")
        return redirect("menu:plato_lista")


# ---------- Gestión de categorías ----------
class CategoriaListView(AdministradorRequeridoMixin, ListView):
    model = Categoria
    template_name = "menu/categoria_lista.html"
    context_object_name = "categorias"
    extra_context = {"seccion": "gestion_menu"}


class CategoriaCreateView(AdministradorRequeridoMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "menu/formulario.html"
    success_url = reverse_lazy("menu:categoria_lista")
    extra_context = {"seccion": "gestion_menu", "titulo": "Nueva categoría", "volver": reverse_lazy("menu:categoria_lista")}

    def form_valid(self, form):
        messages.success(self.request, "Categoría creada.")
        return super().form_valid(form)


class CategoriaUpdateView(AdministradorRequeridoMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "menu/formulario.html"
    success_url = reverse_lazy("menu:categoria_lista")
    extra_context = {"seccion": "gestion_menu", "titulo": "Editar categoría", "volver": reverse_lazy("menu:categoria_lista")}

    def form_valid(self, form):
        messages.success(self.request, "Categoría actualizada.")
        return super().form_valid(form)


class CategoriaDeleteView(AdministradorRequeridoMixin, DeleteView):
    model = Categoria
    template_name = "menu/confirmar_eliminar.html"
    success_url = reverse_lazy("menu:categoria_lista")
    extra_context = {"seccion": "gestion_menu", "volver": reverse_lazy("menu:categoria_lista")}

    def form_valid(self, form):
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar: la categoría tiene platos. Muévelos o elimínalos primero.")
            return redirect("menu:categoria_lista")
        messages.success(self.request, "Categoría eliminada.")
        return respuesta
