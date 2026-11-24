# Imagen de producción del SIGR en dos etapas: la primera instala las dependencias y la segunda
# solo copia el entorno ya listo, así la imagen final no lleva herramientas de compilación.

FROM python:3.12-slim AS construccion
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt requirements-prod.txt ./
RUN pip install -r requirements-prod.txt


FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
# El disco de un contenedor no es persistente: las fotos subidas se guardan en la base de datos.
ENV SIGR_MEDIA_EN_BD=1

# Usuario sin privilegios: si alguien vulnera la aplicación no es administrador del contenedor.
RUN useradd --system --create-home --home-dir /app --uid 10001 sigr
WORKDIR /app
COPY --from=construccion /opt/venv /opt/venv
COPY --chown=sigr:sigr . .
USER sigr

# Estilos y archivos estáticos se generan al construir la imagen (no necesitan base de datos).
# La clave de esta línea es solo de construcción: la real llega por variable de entorno al ejecutar.
RUN python manage.py compilar_scss \
    && DJANGO_DEBUG=0 DJANGO_SECRET_KEY=clave-solo-para-construir-la-imagen python manage.py collectstatic --noinput \
    && mkdir -p media

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 CMD ["python", "docker/healthcheck.py"]
ENTRYPOINT ["sh", "docker/entrypoint.sh"]
