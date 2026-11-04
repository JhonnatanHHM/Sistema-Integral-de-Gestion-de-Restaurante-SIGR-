class FiltrosEnPaginacionMixin:
    """Agrega `querystring` (filtros actuales sin `page`) para armar los enlaces del paginador."""

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        parametros.pop("parcial", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto
