# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

## [0.1.0] - 2026-11-04

### Añadido
- Flujo de trabajo Git: ramas `main` y `dev`, plantillas de Pull Request e Issues, guardia de ramas en GitHub Actions y guía `CONTRIBUTING.md`.
- Proyecto Django (monolito MTV) con paquetes `config/` y `apps/`, configuración por variables de entorno y conexión a PostgreSQL.
- App `panel` con página de inicio y su prueba.
- Plantillas base (`base.html`, encabezado y pie) y estilos SCSS con paleta oscura/dorada, más el comando `compilar_scss`.
- `.env.example`, `.gitignore`, `requirements.txt` y `README.md` con la puesta en marcha.
- `settings_test.py` para ejecutar las pruebas sobre SQLite en memoria.
