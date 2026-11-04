# SIGR · Sistema Integral de Gestión de Restaurante

Aplicación web para gestionar pedidos, reservas, administración de menús, control de caja y generación de reportes.

Proyecto de la materia *Gestión del Software* (Tecnológica del Oriente). Su primer hito estable es la **línea base v1.0.0**: ver [docs/linea-base.md](docs/linea-base.md).

## Módulos

| Módulo | Qué hace | Quién lo usa |
|---|---|---|
| **Autenticación** | Registro, ingreso con correo, perfil y roles | Todos |
| **Menú digital** | Carta pública con búsqueda; CRUD de platos y categorías; platos agotados | Visitantes y cliente (carta), mesero (disponibilidad), administrador (gestión) |
| **Pedidos** | Pedido por mesa, estados Pendiente → En preparación → Listo → Servido → Cerrado, cancelación y pantallas que se actualizan solas | Cliente y personal |
| **Reservas** | Reserva por fecha y hora (franjas de 30 min, 2 h de duración), sin cruces de mesa ni de cliente | Cliente reserva; personal confirma y completa |
| **Caja y reportes** | Factura numerada al cerrar un pedido, cierre de caja diario inmutable, reportes de ventas y platos más vendidos | Mesero (total del día), administrador (todo) |

Roles: **cliente** (se registra solo), **mesero** y **administrador** (los crea el administrador).

## Arquitectura

Monolito **MTV en Django 5.2** con **PostgreSQL** y estilos en **SCSS**. Una app por módulo en `apps/`, permisos con mixins por rol, y todas las entradas validadas y normalizadas con formularios de Django (sin SQL armado a mano). Detalle en [docs/arquitectura.md](docs/arquitectura.md).

## Puesta en marcha (Windows, PowerShell)

Requisitos: Python 3.10 a 3.12, PostgreSQL 14+ y Git.

```powershell
git clone https://github.com/JhonnatanHHM/Sistema-Integral-de-Gestion-de-Restaurante-SIGR-.git
cd Sistema-Integral-de-Gestion-de-Restaurante-SIGR-
```

1. **Base de datos** (en pgAdmin o `psql`, sobre la base `postgres`):
   ```sql
   CREATE USER sigr_app WITH PASSWORD 'cambia-esta-contrasena' CREATEDB;
   CREATE DATABASE sigr OWNER sigr_app ENCODING 'UTF8';
   ```
2. **Variables de entorno:** copia `.env.example` como `.env` y rellénalo (conexión a PostgreSQL y `DJANGO_SECRET_KEY`).
3. **Entorno de Python:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
4. **Tablas, administrador y datos de ejemplo:**
   ```powershell
   .venv\Scripts\python manage.py migrate
   .venv\Scripts\python manage.py createsuperuser
   .venv\Scripts\python manage.py cargar_menu_demo      # opcional: menú de ejemplo
   .venv\Scripts\python manage.py runserver
   ```
5. Abre http://127.0.0.1:8000/ e inicia sesión en `/cuentas/ingresar/`.

El primer administrador se crea con `createsuperuser`; después, desde **Usuarios → Nuevo personal**, el administrador da de alta a los meseros. Para instalar en un servidor, ver el [manual de despliegue](docs/despliegue.md).

## Pantallas principales

| Ruta | Descripción |
|---|---|
| `/` | Inicio: bienvenida, platos destacados con foto y accesos según tu rol |
| `/menu/` | Carta pública |
| `/pedidos/nuevo/`, `/pedidos/` | Crear pedidos y seguirlos |
| `/reservas/nueva/`, `/reservas/` | Reservar y gestionar reservas |
| `/caja/` | Ventas del día; el administrador además cierra la caja y consulta facturas, cierres y reportes |
| `/menu/gestion/platos/` | Gestión del menú (personal) |
| `/cuentas/usuarios/` | Usuarios y alta de personal (administrador) |

## Fotos de los platos
El administrador sube la foto de cada plato al crearlo o editarlo (**Gestión del menú → Editar**) y puede marcarlo como **destacado** para que salga en el inicio (máximo 6). Se aceptan JPG, PNG o WebP de hasta 2 MB y 4000 px por lado. Un plato sin foto muestra un marcador elegante con su inicial. Las fotos se guardan en `media/` (no se versiona).

## Reglas de negocio que conviene conocer
- **Pedidos:** mesa de 1 a 99, cantidades de 1 a 50; el precio se toma del menú en el momento de pedir y no cambia después. Solo se cancela un pedido pendiente.
- **Reservas:** de 11:00 a 20:00 cada 30 minutos, con entre 1 hora y 30 días de anticipación, hasta 12 personas. Una mesa no se reserva dos veces dentro de 2 horas.
- **Caja:** al cerrar un pedido se emite su factura. El cierre de caja compara el efectivo contado con las ventas del día, no se puede modificar ni repetir, y no se permite con pedidos del día sin cerrar. Con la caja cerrada no se pueden cerrar más pedidos ese día. No se manejan impuestos.

## Estilos
```powershell
.venv\Scripts\python manage.py compilar_scss          # compila una vez
.venv\Scripts\python manage.py compilar_scss --watch  # recompila al guardar
```
El CSS compilado (`static/css/sigr.css`) se versiona; recompílalo y súbelo cuando cambies el SCSS.

## Pruebas
```powershell
.venv\Scripts\python manage.py test --settings=config.settings_test   # rápidas, SQLite en memoria
.venv\Scripts\python manage.py test --settings=config.settings_ci     # sobre PostgreSQL (lo mismo que el CI)
```
Incluyen pruebas unitarias por módulo y pruebas de integración de extremo a extremo (`apps/integracion`). En GitHub, el flujo `pruebas` las ejecuta en cada Pull Request y su resultado es obligatorio para fusionar. Para una revisión a mano, ver [docs/verificacion-manual.md](docs/verificacion-manual.md).

## Flujo de trabajo y versionado
`rama nueva → dev → main`, siempre por Pull Request, con los checks `origen-permitido` y `pruebas` obligatorios. Commits en formato Conventional Commits y versiones con SemVer (tags `vX.Y.Z`). Ver [CONTRIBUTING.md](CONTRIBUTING.md) y [CHANGELOG.md](CHANGELOG.md).

## Documentación

| Documento | Contenido |
|---|---|
| [docs/linea-base.md](docs/linea-base.md) | Definición y criterios de la línea base |
| [docs/arquitectura.md](docs/arquitectura.md) | Arquitectura, estructura de carpetas y convenciones |
| [docs/base-de-datos.md](docs/base-de-datos.md) | Diagrama entidad–relación y diccionario de datos |
| [docs/despliegue.md](docs/despliegue.md) | Manual de despliegue en Windows y en Linux |
| [docs/verificacion-manual.md](docs/verificacion-manual.md) | Lista de comprobación manual |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios por versión |

## Licencia
MIT © 2026 Jhonnatan Hernando Henao Montoya. Ver [LICENSE](LICENSE).
