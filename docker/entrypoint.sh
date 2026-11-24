#!/bin/sh
# Arranque del contenedor: aplica migraciones y levanta gunicorn.
#   PORT             puerto de escucha (Render lo define; por defecto 8000)
#   WEB_CONCURRENCY  procesos de gunicorn (por defecto 2)
#   SIGR_CARGAR_DEMO 1 para cargar el menú de demostración (idempotente); solo para staging
#   SIGR_ADMIN_EMAIL / SIGR_ADMIN_PASSWORD  crean el administrador inicial si no existe (ver crear_admin_inicial)
set -e

python manage.py migrate --noinput

if [ "${SIGR_CARGAR_DEMO:-0}" = "1" ]; then
    python manage.py cargar_menu_demo
fi

if [ -n "${SIGR_ADMIN_EMAIL:-}" ] && [ -n "${SIGR_ADMIN_PASSWORD:-}" ]; then
    python manage.py crear_admin_inicial || echo "AVISO: no se pudo crear el administrador inicial; el servicio arranca igual."
fi

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --access-logfile -
