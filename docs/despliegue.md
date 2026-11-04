# Manual de despliegue

Dos escenarios: **A. instalación local (Windows)**, la que se usó durante el desarrollo, y **B. servidor Linux de producción** con gunicorn, nginx y systemd.

> Estado de validación: el escenario A se ejecutó completo en el equipo de desarrollo, y la configuración de producción se verificó con `python manage.py check --deploy` y `collectstatic`. Los archivos de nginx y systemd del escenario B son una configuración de referencia: ajusta dominios y rutas a tu servidor.

## Requisitos

| Componente | Versión |
|---|---|
| Python | 3.10 a 3.12 |
| PostgreSQL | 14 o superior (probado con 16 y 18) |
| Git | cualquiera reciente |
| Producción | nginx y un dominio con certificado HTTPS |

## Variables de entorno

Se leen del archivo `.env` (en la carpeta del proyecto) o del entorno del sistema. Plantilla: `.env.example`.

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Sí | Conexión a PostgreSQL |
| `DJANGO_SECRET_KEY` | Sí | Cadena larga y aleatoria. Con `DJANGO_DEBUG=0` el sistema **se niega a arrancar** con la clave por defecto |
| `DJANGO_DEBUG` | No | `1` en desarrollo (por defecto); **`0` en producción** |
| `DJANGO_ALLOWED_HOSTS` | Sí en producción | Dominios permitidos, separados por comas |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Sí en producción | Orígenes con https que envían formularios, p. ej. `https://sigr.ejemplo.com` |
| `DJANGO_BEHIND_PROXY` | Con nginx | `1` si el proxy termina el HTTPS y envía `X-Forwarded-Proto` |
| `DJANGO_SSL_REDIRECT` | No | Redirigir http→https; `1` por defecto con `DJANGO_DEBUG=0` |
| `DJANGO_HSTS_SECONDS` | No | Duración de HSTS; `31536000` por defecto con `DJANGO_DEBUG=0` |

Generar una clave secreta:
```
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## A. Instalación local (Windows, PowerShell)

1. **Clonar el repositorio**
   ```powershell
   git clone https://github.com/JhonnatanHHM/Sistema-Integral-de-Gestion-de-Restaurante-SIGR-.git
   cd Sistema-Integral-de-Gestion-de-Restaurante-SIGR-
   ```
2. **Base de datos.** En pgAdmin o `psql`, sobre la base `postgres`:
   ```sql
   CREATE USER sigr_app WITH PASSWORD 'cambia-esta-contrasena' CREATEDB;
   CREATE DATABASE sigr OWNER sigr_app ENCODING 'UTF8';
   ```
   (`CREATEDB` permite que las pruebas creen su base temporal.)
3. **Variables de entorno.** `copy .env.example .env` y edita los valores.
4. **Entorno de Python**
   ```powershell
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
5. **Tablas, administrador y datos de ejemplo**
   ```powershell
   .venv\Scripts\python manage.py migrate
   .venv\Scripts\python manage.py createsuperuser
   .venv\Scripts\python manage.py cargar_menu_demo      # opcional
   ```
6. **Arrancar:** `.venv\Scripts\python manage.py runserver` y abrir http://127.0.0.1:8000/
7. **Verificar:** `.venv\Scripts\python manage.py test --settings=config.settings_ci` (debe terminar en `OK`) y seguir la [guía de verificación manual](verificacion-manual.md).

---

## B. Producción en Linux (Ubuntu/Debian)

### 1. Paquetes y usuario del sistema
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev libpq-dev postgresql nginx git
sudo adduser --system --group --home /opt/sigr sigr
```

### 2. Base de datos
```bash
sudo -u postgres psql <<'SQL'
CREATE USER sigr_app WITH PASSWORD 'CONTRASEÑA-FUERTE';
CREATE DATABASE sigr OWNER sigr_app ENCODING 'UTF8';
SQL
```

### 3. Código y entorno
```bash
sudo -u sigr git clone https://github.com/JhonnatanHHM/Sistema-Integral-de-Gestion-de-Restaurante-SIGR-.git /opt/sigr/app
cd /opt/sigr/app
sudo -u sigr git checkout v1.0.0            # siempre desplegar una versión etiquetada
sudo -u sigr python3 -m venv /opt/sigr/venv
sudo -u sigr /opt/sigr/venv/bin/pip install -r requirements-prod.txt
```

### 4. Configuración
Crear `/opt/sigr/app/.env` (permisos `600`, dueño `sigr`):
```ini
DB_NAME=sigr
DB_USER=sigr_app
DB_PASSWORD=CONTRASEÑA-FUERTE
DB_HOST=localhost
DB_PORT=5432
DJANGO_SECRET_KEY=<clave generada>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=sigr.ejemplo.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://sigr.ejemplo.com
DJANGO_BEHIND_PROXY=1
```

### 5. Tablas, estáticos y administrador
```bash
cd /opt/sigr/app
sudo -u sigr /opt/sigr/venv/bin/python manage.py migrate
sudo -u sigr /opt/sigr/venv/bin/python manage.py collectstatic --noinput
sudo -u sigr /opt/sigr/venv/bin/python manage.py createsuperuser
sudo -u sigr /opt/sigr/venv/bin/python manage.py check --deploy
```
`check --deploy` debe mostrar solo dos avisos opcionales (HSTS para subdominios y *preload*); actívalos únicamente si todos tus subdominios usan HTTPS.

### 6. Servicio (systemd)
`/etc/systemd/system/sigr.service`:
```ini
[Unit]
Description=SIGR (gunicorn)
After=network.target postgresql.service

[Service]
User=sigr
Group=sigr
WorkingDirectory=/opt/sigr/app
ExecStart=/opt/sigr/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sigr
```

### 7. nginx
`/etc/nginx/sites-available/sigr`:
```nginx
server {
    listen 80;
    server_name sigr.ejemplo.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name sigr.ejemplo.com;
    # ssl_certificate y ssl_certificate_key: por ejemplo con certbot (Let's Encrypt)

    location /static/ {
        alias /opt/sigr/app/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/sigr /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 8. Comprobación
Abrir `https://sigr.ejemplo.com/` (debe cargar con estilos), iniciar sesión como administrador y recorrer la [guía de verificación manual](verificacion-manual.md).

---

## Actualizar a una versión nueva
```bash
cd /opt/sigr/app
sudo -u sigr git fetch --tags
sudo -u sigr git checkout vX.Y.Z
sudo -u sigr /opt/sigr/venv/bin/pip install -r requirements-prod.txt
sudo -u sigr /opt/sigr/venv/bin/python manage.py migrate
sudo -u sigr /opt/sigr/venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart sigr
```
Antes de actualizar, haz una copia de seguridad de la base de datos.

## Volver a una versión anterior
1. Detener el servicio: `sudo systemctl stop sigr`.
2. Restaurar la copia de la base de datos hecha antes de actualizar (las migraciones nuevas pueden no ser reversibles).
3. `git checkout vX.Y.Z` (la versión anterior), reinstalar dependencias y `collectstatic`.
4. `sudo systemctl start sigr`.

## Copias de seguridad
```bash
# Copia
pg_dump -U sigr_app -h localhost -Fc sigr > sigr_$(date +%F).dump
# Restauración (sobre una base vacía)
pg_restore -U sigr_app -h localhost -d sigr --clean --if-exists sigr_2026-11-04.dump
```
Programa la copia diaria (cron o systemd timer) y guárdala fuera del servidor. Los cierres de caja y las facturas son datos contables: no se borran.

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ImproperlyConfigured: Define DJANGO_SECRET_KEY…` | `DJANGO_DEBUG=0` con la clave por defecto | Definir `DJANGO_SECRET_KEY` en `.env` |
| Error 400 «Bad Request» | Dominio fuera de `DJANGO_ALLOWED_HOSTS` | Agregar el dominio |
| Error 403 «CSRF verification failed» al enviar formularios | Falta `DJANGO_CSRF_TRUSTED_ORIGINS` o `DJANGO_BEHIND_PROXY` | Definirlas y reiniciar |
| Bucle de redirecciones | HTTPS terminado en nginx sin `DJANGO_BEHIND_PROXY=1` | Activarla y enviar `X-Forwarded-Proto` |
| Página sin estilos | No se ejecutó `collectstatic` o falta el `location /static/` | Ejecutarlo y revisar nginx |
| `password authentication failed` | Credenciales de `.env` distintas a las de PostgreSQL | Corregir `DB_USER`/`DB_PASSWORD` |
| Las pruebas no pueden crear la base | El usuario no tiene `CREATEDB` | `ALTER USER sigr_app CREATEDB;` |
