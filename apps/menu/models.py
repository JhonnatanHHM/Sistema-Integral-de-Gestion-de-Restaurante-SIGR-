from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower

from apps.comun.validators import validar_nombre_comercial, validar_texto_libre


class Categoria(models.Model):
    nombre = models.CharField("nombre", max_length=60, validators=[validar_nombre_comercial])
    descripcion = models.CharField("descripción", max_length=200, blank=True, validators=[validar_texto_libre])
    orden = models.PositiveSmallIntegerField("orden", default=0, validators=[MaxValueValidator(999)])
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["orden", "nombre"]
        constraints = [models.UniqueConstraint(Lower("nombre"), name="categoria_nombre_unico_ci")]

    def __str__(self):
        return self.nombre


class Plato(models.Model):
    categoria = models.ForeignKey(Categoria, verbose_name="categoría", on_delete=models.PROTECT, related_name="platos")
    nombre = models.CharField("nombre", max_length=100, validators=[validar_nombre_comercial])
    descripcion = models.CharField("descripción", max_length=500, blank=True, validators=[validar_texto_libre])
    precio = models.DecimalField(
        "precio",
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("9999999.99"))],
    )
    disponible = models.BooleanField("disponible", default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "plato"
        verbose_name_plural = "platos"
        ordering = ["categoria__orden", "categoria__nombre", "nombre"]
        constraints = [models.UniqueConstraint(Lower("nombre"), "categoria", name="plato_nombre_unico_por_categoria_ci")]

    def __str__(self):
        return self.nombre
