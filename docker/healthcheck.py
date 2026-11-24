"""Comprobación de salud del contenedor: consulta /salud/ y sale con 0 (sano) o 1 (enfermo).

Envía como Host el primer dominio de DJANGO_ALLOWED_HOSTS para que Django no rechace la petición."""
import os
import sys
import urllib.request

host = (os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")[0].strip()) or "localhost"
url = f"http://127.0.0.1:{os.environ.get('PORT', '8000')}/salud/"

try:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Host": host}), timeout=4) as respuesta:
        sys.exit(0 if respuesta.status == 200 else 1)
except Exception:
    sys.exit(1)
