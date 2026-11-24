"""Prueba de carga del SIGR con Locust: usuarios anónimos que recorren las páginas públicas.

Ejecución local (con el sistema levantado en el puerto 8000):
    locust -f carga/locustfile.py --headless -u 20 -r 5 -t 30s --host http://localhost:8000

Umbrales (variables de entorno): si se superan, Locust termina con código 1 y el pipeline falla.
    CARGA_P95_MS      percentil 95 máximo del tiempo de respuesta, en ms (por defecto 1000)
    CARGA_MAX_FALLOS  proporción máxima de peticiones fallidas (por defecto 0.01 = 1 %)
"""
import os

from locust import HttpUser, between, events, task

P95_MAXIMO_MS = float(os.environ.get("CARGA_P95_MS", "1000"))
FALLOS_MAXIMOS = float(os.environ.get("CARGA_MAX_FALLOS", "0.01"))


class VisitanteAnonimo(HttpUser):
    """Un visitante que mira la carta, el inicio y las pantallas de ingreso, con pausas humanas entre acciones."""

    wait_time = between(0.5, 2)

    @task(5)
    def carta_publica(self):
        self.client.get("/menu/", name="/menu/")

    @task(3)
    def inicio(self):
        self.client.get("/", name="/")

    @task(1)
    def ingreso(self):
        self.client.get("/cuentas/ingresar/", name="/cuentas/ingresar/")

    @task(1)
    def salud(self):
        self.client.get("/salud/", name="/salud/")


@events.quitting.add_listener
def validar_umbrales(environment, **kwargs):
    """Convierte los umbrales de rendimiento en un resultado de aprobado/reprobado."""
    total = environment.stats.total
    p95 = total.get_response_time_percentile(0.95) or 0
    print(f"\nPeticiones: {total.num_requests} | fallos: {total.fail_ratio:.2%} | p95: {p95:.0f} ms "
          f"(umbrales: p95 <= {P95_MAXIMO_MS:.0f} ms, fallos <= {FALLOS_MAXIMOS:.0%})")
    if total.num_requests == 0:
        environment.process_exit_code = 1
        print("FALLO: no se completó ninguna petición.")
    elif total.fail_ratio > FALLOS_MAXIMOS:
        environment.process_exit_code = 1
        print("FALLO: demasiadas peticiones fallidas.")
    elif p95 > P95_MAXIMO_MS:
        environment.process_exit_code = 1
        print("FALLO: el percentil 95 supera el umbral de rendimiento.")
    else:
        print("APROBADO: rendimiento dentro de los umbrales.")
