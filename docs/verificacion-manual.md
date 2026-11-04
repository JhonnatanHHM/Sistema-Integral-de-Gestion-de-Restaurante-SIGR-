# Guía de verificación manual

Complementa las pruebas automáticas. Sirve para validar la línea base en un entorno recién instalado.
Requisitos: sistema en marcha (ver el [README](../README.md)) y datos de ejemplo cargados con `python manage.py cargar_menu_demo`.

## Preparación
1. Crear el administrador: `python manage.py createsuperuser` (correo, nombre, apellido y contraseña).
2. Iniciar sesión en `/cuentas/ingresar/`.
3. Desde **Usuarios → Nuevo personal**, crear un mesero.
4. Cerrar sesión y registrar un cliente en `/cuentas/registro/`.

## Lista de comprobación

| # | Módulo | Qué hacer | Resultado esperado | ¿OK? |
|---|--------|-----------|--------------------|------|
| 1 | Autenticación | Registrar un cliente con correo `sin-arroba` | Mensaje de correo inválido; no se crea la cuenta | ☐ |
| 2 | Autenticación | Registrar un cliente con nombre `Ana1` | Mensaje de que solo se permiten letras | ☐ |
| 3 | Autenticación | Iniciar sesión con contraseña incorrecta | Mensaje de credenciales inválidas | ☐ |
| 4 | Autenticación | Como cliente, abrir `/cuentas/usuarios/` | Página «Acceso denegado» (403) | ☐ |
| 5 | Menú | Abrir `/menu/` sin sesión | Se ve la carta con los platos disponibles | ☐ |
| 6 | Menú | Buscar `' OR 1=1 --` | Mensaje de caracteres no permitidos y sin resultados | ☐ |
| 7 | Menú | Como administrador, crear un plato con precio `abc`, `-5` o `0` | Se rechaza el precio | ☐ |
| 8 | Menú | Como mesero, marcar un plato como agotado | Desaparece de la carta pública | ☐ |
| 9 | Menú | Como mesero, intentar crear un plato | Acceso denegado (403) | ☐ |
| 10 | Pedidos | Como cliente, pedir 2 platos para la mesa 5 | Pedido «Pendiente» con total correcto | ☐ |
| 11 | Pedidos | Pedir con mesa `0` o `100`, o cantidad `51` | Se rechaza; no se crea el pedido | ☐ |
| 12 | Pedidos | Como mesero, avanzar el pedido hasta «Cerrado» | Cada clic avanza un solo paso; al cerrar se emite la factura | ☐ |
| 13 | Pedidos | Con el detalle abierto en dos pestañas, avanzar en una y luego en la otra | La segunda avisa que el estado cambió y no salta pasos | ☐ |
| 14 | Pedidos | Dejar abierta la lista de pedidos mientras otra persona crea uno | La lista se actualiza sola en pocos segundos | ☐ |
| 15 | Pedidos | Como cliente, abrir el pedido de otro cliente (cambiando el número en la URL) | Página no encontrada (404) | ☐ |
| 16 | Reservas | Reservar mesa 6 mañana a las 13:00 | Reserva «Pendiente» | ☐ |
| 17 | Reservas | Reservar la misma mesa a las 14:00 de ese día | Se rechaza por cruce de horario | ☐ |
| 18 | Reservas | Reservar la misma mesa a las 15:00 | Se acepta (la anterior termina a las 15:00) | ☐ |
| 19 | Reservas | Reservar con hora `10:30`, fecha pasada o a más de 30 días | Se rechaza | ☐ |
| 20 | Reservas | Como mesero, confirmar y luego completar la reserva | Cambia de estado; el cliente no ve esos botones | ☐ |
| 21 | Caja | Como mesero, abrir `/caja/` | Solo se ve el total de ventas del día | ☐ |
| 22 | Caja | Como administrador, abrir `/caja/reportes/` | Ventas por día, ticket promedio y platos más vendidos | ☐ |
| 23 | Caja | Reporte con rango `2026-12-31` a `2026-01-01` | Mensaje de rango inválido | ☐ |
| 24 | Caja | Cerrar la caja con un pedido sin cerrar ese día | Se rechaza e indica cuántos pedidos faltan | ☐ |
| 25 | Caja | Cerrar la caja con efectivo `abc` o `-1` | Se rechaza | ☐ |
| 26 | Caja | Cerrar la caja con el efectivo correcto | «Cuadrado»; con otro valor, «Sobrante» o «Faltante» | ☐ |
| 27 | Caja | Intentar cerrar la caja del mismo día otra vez | Se rechaza: ya fue cerrada | ☐ |
| 28 | Caja | Tras cerrar la caja, intentar cerrar otro pedido | Se rechaza: la caja de hoy ya está cerrada | ☐ |
| 29 | Factura | Abrir la factura de un pedido cerrado e imprimirla | Se ve numerada y se imprime sin menús ni botones | ☐ |

## Evidencia
Para el informe, anotar la fecha de la verificación, quién la hizo y capturar las pantallas de los puntos 10, 12, 17, 22, 26 y 29.
