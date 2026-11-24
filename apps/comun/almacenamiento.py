"""Almacenamiento de archivos subidos en la base de datos, para despliegues sin disco persistente.

Se activa con la variable de entorno SIGR_MEDIA_EN_BD=1 (la imagen Docker ya la trae activada). Las fotos son pocas y se
validan a 2 MB como máximo, así que la base de datos las aguanta sin necesidad de un servicio de almacenamiento externo.
Es un `Storage` de Django: los modelos, formularios y plantillas no cambian, y `imagen.url` sigue apuntando a /media/...
"""
import mimetypes
from urllib.parse import quote

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from .models import ArchivoMedia


@deconstructible
class AlmacenEnBaseDeDatos(Storage):
    def _open(self, name, mode="rb"):
        archivo = ArchivoMedia.objects.get(nombre=name)
        return ContentFile(bytes(archivo.contenido), name=name)

    def _save(self, name, content):
        content.seek(0)
        tipo = mimetypes.guess_type(name)[0] or "application/octet-stream"
        ArchivoMedia.objects.update_or_create(nombre=name, defaults={"contenido": content.read(), "tipo": tipo})
        return name

    def exists(self, name):
        return ArchivoMedia.objects.filter(nombre=name).exists()

    def delete(self, name):
        ArchivoMedia.objects.filter(nombre=name).delete()

    def size(self, name):
        return len(bytes(ArchivoMedia.objects.get(nombre=name).contenido))

    def url(self, name):
        return settings.MEDIA_URL + quote(name)
