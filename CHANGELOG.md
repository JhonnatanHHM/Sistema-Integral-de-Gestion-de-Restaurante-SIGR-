# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

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
