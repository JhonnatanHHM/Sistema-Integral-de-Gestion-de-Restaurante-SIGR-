# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

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
