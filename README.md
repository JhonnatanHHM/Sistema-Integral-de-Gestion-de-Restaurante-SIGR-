# SIGR · Sistema Integral de Gestión de Restaurante

Aplicación web para gestionar pedidos, reservas, administración de menús, control de caja y generación de reportes.

## Arquitectura
- **Django (MTV)**: monolito con una app por módulo en `apps/` (`panel` por ahora; irán `usuarios`, `menu`, `pedidos`, `reservas` y `caja`).
- **PostgreSQL** como base de datos.
- **SCSS** en `static/scss/`, compilado a `static/css/sigr.css` (el CSS compilado se versiona).
- Configuración por variables de entorno (`.env`, no se sube a git).

## Puesta en marcha (Windows, PowerShell)

### 1. Base de datos
En pgAdmin o `psql`, sobre la base `postgres`:
```sql
CREATE USER sigr_app WITH PASSWORD 'cambia-esta-contrasena' CREATEDB;
CREATE DATABASE sigr OWNER sigr_app ENCODING 'UTF8';
```

### 2. Variables de entorno
Copia `.env.example` como `.env` y rellénalo (conexión a PostgreSQL y `DJANGO_SECRET_KEY`).

### 3. Entorno de Python (3.10 a 3.12)
```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 4. Tablas y servidor
```powershell
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py createsuperuser
.venv\Scripts\python manage.py runserver
```
Abre http://127.0.0.1:8000/.

### Roles y acceso
Las cuentas usan correo y contraseña. Roles: **cliente** (se crea desde `/cuentas/registro/`), **mesero** y **administrador**. El primer administrador se crea con `createsuperuser`; después, desde `/cuentas/usuarios/`, el administrador da de alta al personal.
Los permisos de las vistas se manejan con mixins de `apps/usuarios/mixins.py`.

### Menú digital
La carta pública está en `/menu/`. El personal gestiona los platos en `/menu/gestion/platos/` (el mesero marca disponibilidad; el administrador además crea, edita y elimina platos y categorías). Para cargar datos de ejemplo:
```powershell
.venv\Scripts\python manage.py cargar_menu_demo
```

### Pedidos
Cualquier usuario con sesión crea un pedido en `/pedidos/nuevo/` (mesa y cantidad por plato). El cliente ve y cancela (mientras esté pendiente) solo los suyos; el mesero y el administrador ven todos y avanzan el estado: Pendiente → En preparación → Listo → Servido → Cerrado. Las pantallas de pedidos se refrescan solas.

### Reservas
El cliente reserva en `/reservas/nueva/`: fecha, hora (franjas de 30 minutos entre 11:00 y 20:00), personas (1 a 12) y mesa (1 a 99). Cada reserva ocupa la mesa 2 horas y se admite con entre 1 hora y 30 días de anticipación; el sistema impide cruces. El mesero y el administrador ven todas las reservas, las confirman, las completan o las cancelan. Las reglas están en `apps/reservas/reglas.py`.

### Caja, facturas y reportes
Al pasar un pedido a **Cerrado** se emite su factura (`F-000001`…). En `/caja/` el mesero ve el total de ventas del día; el administrador además cierra la caja (`/caja/cierre/nuevo/`: efectivo contado frente a ventas facturadas, sin reabrir), consulta facturas y cierres, y genera reportes de ventas por rango de fechas (`/caja/reportes/`) con los platos más vendidos. No hay impuestos: el total de la factura es la suma de los platos.

### Estilos
```powershell
.venv\Scripts\python manage.py compilar_scss          # compila una vez
.venv\Scripts\python manage.py compilar_scss --watch  # recompila al guardar
```

### Pruebas
```powershell
.venv\Scripts\python manage.py test --settings=config.settings_test   # rápidas, SQLite en memoria
.venv\Scripts\python manage.py test --settings=config.settings_ci     # sobre PostgreSQL (lo mismo que el CI)
```
Incluyen pruebas unitarias por módulo y pruebas de integración de extremo a extremo (`apps/integracion`). En GitHub, el flujo `pruebas` las ejecuta en cada Pull Request y su resultado es obligatorio para fusionar. Para una revisión a mano, ver [docs/verificacion-manual.md](docs/verificacion-manual.md).

## Flujo de trabajo y versionado
Ver [CONTRIBUTING.md](CONTRIBUTING.md) y [CHANGELOG.md](CHANGELOG.md). Flujo: `rama nueva → dev → main`, siempre por Pull Request.

## Licencia
MIT. Ver [LICENSE](LICENSE).
