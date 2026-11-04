# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

## [1.0.0] - 2026-11-04

**Línea base del código fuente del Sistema Integral de Gestión de Restaurante (SIGR).** Primer hito estable del proyecto: a partir de aquí, todo cambio se gestiona como una solicitud de cambio y se publica con una versión nueva.

### Incluye
- Autenticación de usuarios con roles de cliente, mesero y administrador (`0.2.0`).
- Menú digital con CRUD de platos y categorías (`0.3.0`).
- Registro y seguimiento de pedidos con actualización automática (`0.4.0`).
- Reservas por fecha y hora con bloqueo de cruces (`0.5.0`).
- Facturación, cierre de caja y reportes de ventas (`0.6.0`).
- Pruebas de integración, flujo de integración continua sobre PostgreSQL (check obligatorio) y guía de verificación manual (`0.7.0`).
- Documentación técnica: README, estructura de la base de datos, arquitectura y convenciones, manual de despliegue y definición de la línea base (`0.8.0`).

### Verificación de la línea base
- Instalación desde cero a partir de un clon limpio del repositorio, con entorno de Python y base de datos nuevos: `check`, `migrate`, estilos y datos de ejemplo sin errores.
- 212 pruebas automáticas en verde sobre PostgreSQL.
- Servidor en marcha con inicio de sesión de administrador y las pantallas principales respondiendo correctamente.

### Cambiado
- `docs/linea-base.md` registra la fecha de creación de la línea base.

## [0.8.0] - 2026-11-04

### Añadido
- Documentación técnica de la línea base en `docs/`: definición y criterios (`linea-base.md`), arquitectura, estructura de carpetas y convenciones (`arquitectura.md`), diagrama entidad–relación y diccionario de datos (`base-de-datos.md`) y manual de despliegue para Windows y Linux (`despliegue.md`).
- `requirements-prod.txt` con gunicorn para producción.
- Variables de entorno de producción: `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_BEHIND_PROXY` y `DJANGO_HSTS_SECONDS`.

### Cambiado
- README reescrito como documento final: módulos, roles, puesta en marcha, reglas de negocio, pruebas y enlaces a toda la documentación.
- Con `DJANGO_DEBUG=0` el sistema se niega a arrancar con la clave secreta por defecto, y activa HSTS; `check --deploy` queda solo con dos avisos opcionales.
- La licencia MIT pasa a nombrar como titular a Jhonnatan Hernando Henao Montoya.

## [0.7.0] - 2026-11-04

### Añadido
- Pruebas de integración de extremo a extremo (`apps/integracion`): de la cuenta nueva a la reserva, el pedido, la factura, el cierre de caja y el reporte, más cancelaciones, alta de personal y platos agotados.
- Matriz de acceso por rol: verifica qué rol puede abrir cada pantalla y falla si se agrega una ruta sin declarar su permiso.
- Barrido de seguridad: entradas hostiles (inyección SQL, scripts, rutas, plantillas, valores gigantes) en todos los buscadores y formularios; ninguna produce error del servidor ni guarda datos en campos estrictos, y el texto libre se muestra escapado.
- Verificaciones de integridad: sin migraciones pendientes, `check` sin problemas y SCSS compilable.
- Flujo de GitHub Actions `pruebas`: instala dependencias, verifica configuración y migraciones, compila los estilos y ejecuta toda la suite sobre PostgreSQL en cada Pull Request a `dev` y `main`.
- `config/settings_ci.py`: pruebas sobre PostgreSQL real con cifrado de contraseñas rápido (de más de 6 minutos a unos 20 segundos).
- Guía de verificación manual con 29 comprobaciones en `docs/verificacion-manual.md`.
- El check `pruebas` pasa a ser obligatorio en las ramas protegidas, junto con `origen-permitido`.
- 22 pruebas nuevas (212 en total).

## [0.6.0] - 2026-11-04

### Añadido
- App `caja` con los modelos `Factura` y `CierreCaja`.
- Facturación: al cerrar un pedido se emite automáticamente su factura numerada (`F-000001`), una sola por pedido y con el total congelado. La factura se imprime desde el navegador y el cliente puede verla desde su pedido.
- Cierre de caja (solo administrador): registra el efectivo contado, lo compara con las ventas facturadas del día y guarda la diferencia (cuadrado, sobrante o faltante). Un cierre no se puede modificar, eliminar ni repetir para el mismo día.
- Reglas del cierre: no se cierra una fecha futura ni un día con pedidos sin cerrar; con la caja de hoy cerrada ya no se pueden cerrar más pedidos.
- Reportes de ventas (solo administrador): ventas por día, total del período, número de facturas, ticket promedio y platos más vendidos, con rango de fechas validado (formato ISO, desde ≤ hasta ≤ hoy, máximo un año).
- Resumen de caja: el mesero ve solo el total del día; el administrador ve además facturas, pedidos sin cerrar y los accesos de gestión.
- Listados de facturas y de cierres de caja.
- 44 pruebas nuevas: facturación y numeración, diferencias de caja, inmutabilidad de los cierres, totales de reportes, efectivo y fechas mal formados, inyección SQL en filtros y permisos por rol.

### Cambiado
- `MontoField` acepta una cantidad configurable de dígitos (las cajas manejan hasta 10 enteros); su valor por defecto no cambia.

## [0.5.0] - 2026-11-04

### Añadido
- App `reservas` con el modelo `Reserva` (fecha, hora, personas, mesa, notas y estado).
- Reglas de negocio centralizadas: franjas de 11:00 a 20:00 cada 30 minutos, duración de 2 horas, anticipación mínima de 1 hora y máxima de 30 días, hasta 12 personas.
- Bloqueo de cruces: una mesa no se reserva si ya hay una reserva vigente a menos de 2 horas de diferencia (el borde exacto es válido) y un cliente no puede tener dos reservas cruzadas. La verificación se repite dentro de la transacción, con bloqueo en PostgreSQL.
- El cliente crea y cancela sus reservas; el personal ve todas, las confirma, las marca como completadas o las cancela. El cliente y el estado nunca se aceptan desde el formulario.
- Flujo Pendiente → Confirmada → Completada, con cancelación mientras esté vigente; una reserva cancelada libera la mesa.
- Listado con filtros por estado, fecha y mesa, paginación y actualización automática.
- Validación estricta: fecha solo en formato ISO (AAAA-MM-DD), hora solo entre las franjas permitidas, personas y mesa numéricas dentro de su rango, y notas sin `< >`.
- 44 pruebas nuevas, con el reloj fijo: formatos de fecha y hora inválidos, límites de anticipación, cruces y bordes, inyección SQL en filtros, permisos y acciones con pantalla desactualizada.

## [0.4.0] - 2026-11-04

### Añadido
- App `pedidos` con los modelos `Pedido` e `ItemPedido`; el precio de cada ítem se congela al crear el pedido.
- Creación de pedidos desde la carta: el cliente crea el suyo y el mesero registra pedidos de mesa. Mesa entre 1 y 99, cantidades entre 1 y 50 y notas validadas; los precios nunca se reciben del navegador.
- Flujo de estados Pendiente → En preparación → Listo → Servido → Cerrado, con cancelación solo mientras está pendiente.
- Seguimiento con línea de tiempo y actualización automática cada pocos segundos (sin recargar la página).
- Listado con filtros por estado y mesa y paginación; el cliente solo ve sus pedidos (los ajenos responden 404) y el personal ve todos.
- Protección contra doble avance: el botón envía el estado que el usuario veía y el pedido se bloquea durante el cambio.
- Propiedad `es_personal` en `Usuario` y constantes de mesa compartidas en `apps/comun`.
- 38 pruebas nuevas: estados, validación de mesa, cantidades y notas, visibilidad por rol, filtros con inyección SQL y cambios de estado concurrentes.

### Cambiado
- Un plato con pedidos asociados ya no se puede eliminar; se muestra un aviso para marcarlo como agotado.
- El paginador conserva los filtros y omite el parámetro de refresco parcial.

## [0.3.0] - 2026-11-04

### Añadido
- App `menu` con los modelos `Categoria` y `Plato` (nombre único sin distinguir mayúsculas, precio con rango, disponibilidad).
- Menú digital público con búsqueda y filtro por categoría; solo muestra platos disponibles de categorías activas.
- Gestión de platos para el personal: listado con filtros y paginación; el mesero puede marcar platos como disponibles o agotados; el administrador crea, edita y elimina.
- Gestión de categorías para el administrador; no se elimina una categoría que tiene platos.
- App `comun` con utilidades compartidas: `MontoField` (solo dígitos, hasta 2 decimales, positivo, máximo 9 dígitos), validadores de nombres y textos, y paginación que conserva los filtros.
- Comando `cargar_menu_demo` para cargar un menú de ejemplo.
- Estilos de la carta, etiquetas de estado y acciones de tabla.
- 31 pruebas nuevas: precios y textos mal formados, categorías manipuladas, inyección SQL y HTML en búsquedas, y acceso por rol.

### Cambiado
- `limpiar_espacios` pasa a `apps/comun/validators.py` y se reutiliza desde `usuarios`.

## [0.2.0] - 2026-11-04

### Añadido
- App `usuarios` con modelo `Usuario` propio: acceso con correo electrónico y tres roles (cliente, mesero, administrador).
- Inicio de sesión, cierre de sesión (solo POST), registro público y perfil editable.
- Listado de usuarios con búsqueda y filtro por rol, y alta de personal (mesero o administrador), solo para administradores.
- Mixins de permisos por rol (`ClienteRequeridoMixin`, `PersonalRequeridoMixin`, `AdministradorRequeridoMixin`) y página 403.
- Validación y normalización de entradas: correo con formato válido y único sin importar mayúsculas, nombres solo con letras, teléfono de 7 a 15 dígitos, búsqueda con lista de caracteres permitidos.
- Registro público siempre crea clientes; el rol nunca se acepta desde el formulario público.
- Ajustes de seguridad en la configuración (cookies HttpOnly/Secure, `nosniff`, `X-Frame-Options: DENY`).
- Administración de Django para el modelo `Usuario`.
- Estilos de formularios, tablas y paginador.
- 33 pruebas: modelo, formularios con entradas mal formadas e intentos de inyección SQL, y control de acceso por rol.

### Cambiado
- La base de datos de desarrollo parte del modelo de usuario propio (`AUTH_USER_MODEL`).

## [0.1.0] - 2026-11-04

### Añadido
- Flujo de trabajo Git: ramas `main` y `dev`, plantillas de Pull Request e Issues, guardia de ramas en GitHub Actions y guía `CONTRIBUTING.md`.
- Proyecto Django (monolito MTV) con paquetes `config/` y `apps/`, configuración por variables de entorno y conexión a PostgreSQL.
- App `panel` con página de inicio y su prueba.
- Plantillas base (`base.html`, encabezado y pie) y estilos SCSS con paleta oscura/dorada, más el comando `compilar_scss`.
- `.env.example`, `.gitignore`, `requirements.txt` y `README.md` con la puesta en marcha.
- `settings_test.py` para ejecutar las pruebas sobre SQLite en memoria.
