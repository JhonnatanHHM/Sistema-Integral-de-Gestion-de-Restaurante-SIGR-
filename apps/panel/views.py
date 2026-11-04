from django.views.generic import TemplateView


class InicioView(TemplateView):
    template_name = "panel/inicio.html"
    extra_context = {"seccion": "inicio"}
