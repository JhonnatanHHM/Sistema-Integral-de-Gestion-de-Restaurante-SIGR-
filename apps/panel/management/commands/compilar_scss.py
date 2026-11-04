"""Compila static/scss/main.scss a static/css/sigr.css.
Uso: python manage.py compilar_scss [--watch]"""
import time

import sass
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compila los estilos SCSS a CSS"

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true", help="Recompila al detectar cambios")

    def compilar(self):
        origen = settings.BASE_DIR / "static" / "scss"
        destino = settings.BASE_DIR / "static" / "css" / "sigr.css"
        css = sass.compile(filename=str(origen / "main.scss"), output_style="compressed")
        destino.write_text(css, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"CSS generado: {destino.relative_to(settings.BASE_DIR)}"))

    def handle(self, *args, **opciones):
        self.compilar()
        if not opciones["watch"]:
            return
        carpeta = settings.BASE_DIR / "static" / "scss"
        visto = {p: p.stat().st_mtime for p in carpeta.glob("*.scss")}
        self.stdout.write("Vigilando cambios (Ctrl+C para salir)...")
        while True:
            time.sleep(1)
            actual = {p: p.stat().st_mtime for p in carpeta.glob("*.scss")}
            if actual != visto:
                visto = actual
                try:
                    self.compilar()
                except sass.CompileError as error:
                    self.stderr.write(str(error))
