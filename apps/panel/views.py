from django.views.generic import TemplateView

from apps.menu.models import Plato

MAX_DESTACADOS = 6


class InicioView(TemplateView):
    template_name = "panel/inicio.html"
    extra_context = {"seccion": "inicio"}

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        disponibles = Plato.objects.filter(disponible=True, categoria__activa=True).select_related("categoria")
        destacados = list(disponibles.filter(destacado=True)[:MAX_DESTACADOS])
        if not destacados:
            # Sin platos marcados como destacados: se muestran los primeros, con foto primero.
            destacados = sorted(disponibles[:30], key=lambda plato: not plato.imagen)[:MAX_DESTACADOS]
        contexto["destacados"] = destacados
        return contexto
