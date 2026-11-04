from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
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
