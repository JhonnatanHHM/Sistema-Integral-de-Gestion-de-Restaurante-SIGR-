from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.comun.views import salud, servir_media

urlpatterns = [
    path("salud/", salud, name="salud"),
    path("admin/", admin.site.urls),
    path("menu/", include("apps.menu.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
    path("reservas/", include("apps.reservas.urls")),
    path("caja/", include("apps.caja.urls")),
    path("cuentas/", include("apps.usuarios.urls")),
    path("", include("apps.panel.urls")),
]

if settings.DEBUG:
    # En desarrollo Django sirve las fotos subidas; en producción las sirve nginx (ver docs/despliegue.md).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Fotos guardadas en la base de datos (SIGR_MEDIA_EN_BD=1). Sin nombre a propósito: no es una página del sistema.
# Si el almacenamiento es el disco, la tabla está vacía y esta ruta responde 404, igual que antes.
urlpatterns += [path("media/<path:nombre>", servir_media)]
