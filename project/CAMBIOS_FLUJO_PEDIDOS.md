# Cambios aplicados — flujo de pedidos

## Flujo de negocio

1. El mesero inicia sesión y desde un único panel crea pedidos.
2. Cada pedido queda ligado al `camarero_id` del usuario autenticado.
3. El cocinero consulta `/api/v1/orders/kitchen` y puede pasar un pedido `NUEVO` o `EN_COCINA` a `COMPLETADO`.
4. El mesero consulta `/api/v1/orders/mine` y solamente puede marcar como `ENTREGADO` un pedido que él mismo creó y que cocina ya marcó como `COMPLETADO`.
5. El administrador tiene acceso al inventario, gestión de credenciales y `/api/v1/orders/history` para el historial completo.

## Rutas principales para Postman

- `POST /api/v1/users/login`
- `POST /api/v1/orders`
- `GET /api/v1/orders/mine` — solo CAMARERO
- `GET /api/v1/orders/kitchen` — COCINERO/ADMIN
- `PUT /api/v1/orders/{order_id}` con `{ "status": "COMPLETADO" }` — COCINERO
- `PUT /api/v1/orders/{order_id}` con `{ "status": "ENTREGADO" }` — CAMARERO propietario del pedido
- `GET /api/v1/orders/history` — solo ADMIN

También se incluye una colección lista para importar:
`project/postman/Afenix_Flujo_Pedidos.postman_collection.json`

## Frontend

La interfaz ahora se presenta como un único panel principal. Los módulos se generan según el rol autenticado:

- CAMARERO: Pedidos
- COCINERO: Cocina
- ADMIN: Inventario, Usuarios e Historial

El cierre de sesión está disponible desde todas las vistas. Al editar un usuario, el formulario queda resaltado con un borde y halo dorado.

`/admin.html` y `/usuario.html` también sirven la misma interfaz unificada para evitar tener funciones duplicadas en pantallas separadas.
