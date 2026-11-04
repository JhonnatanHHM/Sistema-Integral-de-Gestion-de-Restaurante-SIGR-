from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.usuarios.urls")),
    path("", include("apps.panel.urls")),
]
