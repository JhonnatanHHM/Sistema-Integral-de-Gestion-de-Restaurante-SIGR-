from django.db import models


class ArchivoMedia(models.Model):
    """Archivo subido (foto de un plato) guardado en la base de datos.

    Se usa cuando el sistema corre en un contenedor sin disco persistente, como el plan gratuito de Render: el disco se
    borra en cada reinicio, pero la base de datos no. Ver `apps.comun.almacenamiento.AlmacenEnBaseDeDatos`.
    """

    nombre = models.CharField("nombre", max_length=255, unique=True)       # ruta relativa, p. ej. platos/<aleatorio>.jpg
    contenido = models.BinaryField("contenido")
    tipo = models.CharField("tipo de contenido", max_length=100)
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "archivo subido"
        verbose_name_plural = "archivos subidos"

    def __str__(self):
        return self.nombre
