from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


class FiltrosEnPaginacionMixin:
    """Agrega `querystring` (filtros actuales sin `page`) para armar los enlaces del paginador."""

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        parametros.pop("parcial", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


@require_safe
def salud(request):
    """Estado del servicio para balanceadores y pruebas de humo del pipeline: no pide sesión ni expone datos."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({"estado": "error", "base_de_datos": "no disponible"}, status=503)
    return JsonResponse({"estado": "ok", "base_de_datos": "ok"})
