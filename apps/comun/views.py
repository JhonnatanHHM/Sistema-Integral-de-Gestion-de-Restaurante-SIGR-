from django.db import DatabaseError, connection
from django.http import Http404, HttpResponse, JsonResponse
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


@require_safe
def servir_media(request, nombre):
    """Entrega una foto guardada en la base de datos (ver apps.comun.almacenamiento). Si no existe, 404.

    El nombre solo se usa como clave de búsqueda, nunca como ruta de disco. Las fotos se guardan con un nombre aleatorio
    y una foto reemplazada recibe un nombre nuevo, así que se pueden guardar en caché durante una semana.
    """
    from .models import ArchivoMedia

    try:
        archivo = ArchivoMedia.objects.get(nombre=nombre)
    except ArchivoMedia.DoesNotExist:
        raise Http404("Archivo no encontrado.") from None
    respuesta = HttpResponse(bytes(archivo.contenido), content_type=archivo.tipo)
    respuesta["Cache-Control"] = "no-store"
    return respuesta
