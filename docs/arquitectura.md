# Arquitectura, estructura de carpetas y convenciones

## Arquitectura

Monolito **MTV (Model–Template–View)** con Django 5.2 y PostgreSQL:

```
Navegador ──► Vistas (CBV + mixins de permisos) ──► Formularios (validan y normalizan)
                       │                                       │
                       ▼                                       ▼
                Servicios (reglas de negocio)  ──►  Modelos / ORM  ──►  PostgreSQL
                       │
                       ▼
                Plantillas (HTML + SCSS compilado)
```

- **Model:** datos y restricciones (`models.py`).
- **Template:** plantillas HTML en `templates/` y estilos SCSS en `static/scss/`.
- **View:** vistas basadas en clases en `views.py`; los permisos se declaran con mixins de `apps/usuarios/mixins.py`.
- **Servicios:** las reglas que cruzan varios modelos (crear un pedido, reservar sin cruces, facturar, cerrar caja) viven en `services.py`, no en las vistas.

## Estructura de carpetas

```
.
├── manage.py
├── requirements.txt           dependencias de desarrollo y pruebas
├── requirements-prod.txt      agrega gunicorn para producción
├── .env.example               variables de entorno (el .env real no se versiona)
├── config/                    proyecto Django
│   ├── settings.py            configuración (todo lo variable sale del entorno)
│   ├── settings_test.py       pruebas rápidas sobre SQLite en memoria
│   ├── settings_ci.py         pruebas sobre PostgreSQL (CI)
│   └── urls.py, wsgi.py, asgi.py
├── apps/
│   ├── comun/                 validadores, MontoField y utilidades compartidas
│   ├── usuarios/              cuentas, roles y mixins de permisos
│   ├── menu/                  categorías y platos
│   ├── pedidos/               pedidos, ítems y flujo de estados
│   ├── reservas/              reservas y reglas de horario
│   ├── caja/                  facturas, cierres de caja y reportes
│   ├── panel/                 página de inicio y comando compilar_scss
│   └── integracion/           pruebas de integración de extremo a extremo
├── templates/                 base.html, includes/ y una carpeta por app
├── static/
│   ├── scss/                  código fuente de los estilos
│   ├── css/sigr.css           CSS compilado (se versiona)
│   └── js/tiempo-real.js      refresco automático de pantallas
├── media/                     fotos de los platos subidas (no se versiona)
├── docs/                      documentación técnica
└── .github/                   plantillas de PR e Issues y flujos de GitHub Actions
```

Cada app sigue la misma forma: `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `services.py` (si hay reglas de negocio), `migrations/` y `tests/`.

## Convenciones de código

### Nombres
- Código, plantillas e interfaz en **español** (modelos, campos, vistas, URLs). Las palabras propias de Django (`views`, `urls`, `models`, `forms`) se mantienen.
- Clases en `PascalCase` (`PedidoListView`), funciones y variables en `snake_case`, constantes en `MAYUSCULAS`.
- Nombres de URL con `app:accion` (`pedidos:avanzar`). Plantillas parciales con guion bajo (`_tabla.html`).
- Estilos SCSS con metodología BEM (`.plato__precio`, `.estado--listo`).

### Seguridad (obligatorio en todo cambio)
1. **Entradas validadas y normalizadas.** Todo dato que entra pasa por un `Form` de Django con validadores: correo con formato de correo, dinero solo numérico (`MontoField`), fechas en ISO, horas en franjas fijas, textos con longitud máxima, sin `< >` ni caracteres de control, y espacios limpios.
2. **Sin SQL armado a mano.** Solo ORM con parámetros. Los buscadores validan primero con un formulario; si la entrada no es válida devuelven una lista vacía.
3. **Permisos con mixins.** Toda vista protegida usa `LoginRequiredMixin` o los mixins por rol (`ClienteRequeridoMixin`, `PersonalRequeridoMixin`, `AdministradorRequeridoMixin`). Sin sesión se redirige al ingreso; con el rol equivocado se responde 403; los datos ajenos responden 404.
4. **Nunca confiar en el navegador** para precios, estados, roles o dueños de un registro: se calculan en el servidor.
5. **Archivos subidos validados por su contenido.** Las fotos de platos solo aceptan JPG, PNG o WebP reales (se abren con Pillow y su formato debe coincidir con la extensión), de hasta 2 MB y 4000 px por lado; SVG y cualquier otro formato se rechazan, y el archivo se guarda con un nombre aleatorio (`validar_imagen` en `apps/comun/validators.py`).
6. **Acciones que cambian datos solo por POST**, con token CSRF. Los botones que cambian un estado envían el estado que el usuario veía, para evitar saltos por pantallas desactualizadas.

### Pruebas
- Cada módulo tiene pruebas de modelo, de formularios (incluidas entradas mal formadas y maliciosas) y de vistas (incluidos los permisos por rol).
- Las pruebas que dependen de la hora fijan el reloj con `patch("django.utils.timezone.now")`.
- La matriz de acceso (`apps/integracion/tests/test_matriz_acceso.py`) falla si se agrega una ruta sin declarar qué roles pueden abrirla.
- Antes de abrir un Pull Request: `python manage.py test --settings=config.settings_ci`.

### Git
Flujo, ramas, commits y versionado: ver [CONTRIBUTING.md](../CONTRIBUTING.md).
