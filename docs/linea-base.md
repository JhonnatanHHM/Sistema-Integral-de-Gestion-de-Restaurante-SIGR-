# Línea base del código fuente — SIGR

Documento de referencia de la línea base del **Sistema Integral de Gestión de Restaurante (SIGR)**, el primer hito estable del proyecto, sobre el cual se controlarán los cambios futuros.

| Dato | Valor |
|---|---|
| Sistema | Sistema Integral de Gestión de Restaurante (SIGR) |
| Versión de la línea base | **v1.0.0** |
| Repositorio | https://github.com/JhonnatanHHM/Sistema-Integral-de-Gestion-de-Restaurante-SIGR- |
| Rama estable | `main` |
| Herramienta de versionado | Git y GitHub |
| Licencia | MIT |
| Validado por | Jhonnatan Hernando Henao Montoya (grupo de desarrollo) |
| Responsable de aprobación | Jhonnatan Hernando Henao Montoya |

## Componentes incluidos

| # | Módulo | App Django | Qué incluye |
|---|---|---|---|
| 1 | Autenticación | `usuarios` | Registro, ingreso con correo, perfil, roles (cliente, mesero, administrador) y alta de personal |
| 2 | Menú digital | `menu` | CRUD de categorías y platos, carta pública con búsqueda y control de disponibilidad |
| 3 | Pedidos | `pedidos` | Pedidos por mesa, flujo de estados, cancelación y seguimiento con actualización automática |
| 4 | Reservas | `reservas` | Reservas por fecha y hora, bloqueo de cruces y flujo de estados |
| 5 | Caja y reportes | `caja` | Facturación, cierre de caja diario inmutable y reportes de ventas |

## Historial de versiones hasta la línea base

| Versión | Contenido |
|---|---|
| `v0.1.0` | Flujo de trabajo Git/GitHub y scaffold Django + PostgreSQL |
| `v0.2.0` | Usuarios, autenticación y roles |
| `v0.3.0` | Menú digital |
| `v0.4.0` | Pedidos con seguimiento |
| `v0.5.0` | Reservas |
| `v0.6.0` | Caja, facturación y reportes |
| `v0.7.0` | Pruebas de integración y CI sobre PostgreSQL |
| `v0.8.0` | Documentación técnica final |
| **`v1.0.0`** | **Línea base** |

El detalle de cada versión está en el [CHANGELOG](../CHANGELOG.md); cada una tiene su tag y su release en GitHub.

## Criterios de la línea base

| Criterio | Evidencia |
|---|---|
| Los módulos se instalan y arrancan correctamente | `manage.py check`, `migrate` y `runserver` sin errores; el flujo `pruebas` los ejecuta en cada Pull Request |
| Funcionalidades críticas operativas y validadas | Pruebas de cada módulo y [guía de verificación manual](verificacion-manual.md) |
| Pruebas básicas de integración completadas | `apps/integracion`: flujo completo de punta a punta, matriz de acceso por rol y barrido de seguridad de entradas |
| Estructura de carpetas y convenciones de código definidas | [Arquitectura y convenciones](arquitectura.md) y [CONTRIBUTING](../CONTRIBUTING.md) |
| Documentación técnica mínima adjunta | [README](../README.md), [estructura de la base de datos](base-de-datos.md) y [manual de despliegue](despliegue.md) |
| Historial y licencia | [CHANGELOG](../CHANGELOG.md) y [LICENSE](../LICENSE) (MIT) |

## Control de cambios sobre la línea base

- Cualquier cambio entra por Pull Request de una rama de trabajo hacia `dev`, y de `dev` hacia `main`. No hay commits directos.
- Cada Pull Request debe pasar los checks obligatorios `origen-permitido` y `pruebas`.
- Los cambios se registran en el CHANGELOG y se publican con versionado semántico: correcciones (`1.0.x`), funcionalidades compatibles (`1.x.0`) y cambios incompatibles (`2.0.0`).
- Las nuevas solicitudes de cambio se gestionan con GitHub Issues (plantillas de error y de mejora).
