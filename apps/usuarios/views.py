from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import BusquedaUsuarioForm, LoginForm, PerfilForm, PersonalForm, RegistroForm
from .mixins import AdministradorRequeridoMixin
from .models import Usuario


class AccesoView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = "usuarios/registro.html"
    success_url = reverse_lazy("inicio")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("inicio")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(self.request, "Tu cuenta fue creada. ¡Bienvenido!")
        return respuesta


class PerfilView(LoginRequiredMixin, UpdateView):
    form_class = PerfilForm
    template_name = "usuarios/perfil.html"
    success_url = reverse_lazy("usuarios:perfil")
    extra_context = {"seccion": "perfil"}

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Tus datos fueron actualizados.")
        return super().form_valid(form)


class UsuarioListView(AdministradorRequeridoMixin, ListView):
    model = Usuario
    template_name = "usuarios/lista.html"
    context_object_name = "usuarios"
    paginate_by = 20
    extra_context = {"seccion": "usuarios"}

    def get_formulario(self):
        if not hasattr(self, "_formulario"):
            self._formulario = BusquedaUsuarioForm(self.request.GET or None)
        return self._formulario

    def get_queryset(self):
        consulta = Usuario.objects.all()
        formulario = self.get_formulario()
        if not formulario.is_bound:
            return consulta
        if not formulario.is_valid():
            return consulta.none()
        texto = formulario.cleaned_data["q"]
        rol = formulario.cleaned_data["rol"]
        if texto:
            consulta = consulta.filter(
                Q(first_name__icontains=texto) | Q(last_name__icontains=texto) | Q(email__icontains=texto)
            )
        if rol:
            consulta = consulta.filter(rol=rol)
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["formulario"] = self.get_formulario()
        return contexto


class PersonalCreateView(AdministradorRequeridoMixin, CreateView):
    form_class = PersonalForm
    template_name = "usuarios/personal_form.html"
    success_url = reverse_lazy("usuarios:lista")
    extra_context = {"seccion": "usuarios"}

    def form_valid(self, form):
        messages.success(self.request, "Usuario de personal creado.")
        return super().form_valid(form)
