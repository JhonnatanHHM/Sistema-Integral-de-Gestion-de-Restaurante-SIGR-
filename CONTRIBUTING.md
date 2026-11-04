# Guía de contribución

## Flujo de ramas

```
rama nueva  ──PR──►  dev  ──PR de integración──►  main
```

- `main`: rama estable. Solo recibe Pull Requests desde `dev`. Cada versión se marca con un tag `vX.Y.Z`.
- `dev`: integración. Solo recibe Pull Requests de ramas de trabajo. Se origina desde `main`.
- Cada módulo o cambio vive en una rama creada desde `origin/dev`:
  `feature/<modulo>`, `fix/<descripcion>`, `chore/<descripcion>`, `docs/<descripcion>`, `test/<descripcion>`.
- Nunca se hace push directo a `dev` ni a `main` (protegidas con rulesets en GitHub).
- Estrategia de merge: **squash** en `feature → dev`, **merge commit** en `dev → main`.

## Commits (Conventional Commits)

`tipo(alcance): descripción en imperativo`

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`.

## Versionado (SemVer)

`MAJOR.MINOR.PATCH`. Los hitos de desarrollo son `0.x.0`; la línea base es `v1.0.0`.
Cada versión se registra en `CHANGELOG.md` (formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)) y se publica como tag anotado y release en GitHub.

## Pull Requests

Usa la plantilla del repositorio. Actualiza el CHANGELOG en la sección `[Sin publicar]`.
