"""
EJEMPLOS DE USO DE LA API

Estos son ejemplos práticos de cómo usar todos los endpoints de la API.
Asegúrate de reemplazar <token> con tu JWT token actual.
"""

# ============================
# AUTENTICACIÓN
# ============================

# 1. REGISTRAR UN NUEVO USUARIO
POST http://localhost:8000/api/v1/users/register
Content-Type: application/json

{
  "username": "nuevo_usuario",
  "email": "usuario@restaurant.com",
  "password": "password123",
  "full_name": "Nombre del Usuario",
  "role": "CAMARERO",
  "phone": "1234567890"
}

# Respuesta exitosa:
# {
#   "success": true,
#   "message": "Usuario registrado exitosamente",
#   "data": {
#     "id": 1,
#     "username": "nuevo_usuario",
#     "email": "usuario@restaurant.com",
#     "full_name": "Nombre del Usuario",
#     "role": "CAMARERO",
#     "is_active": true,
#     "phone": "1234567890",
#     "created_at": "2024-01-15T10:30:00",
#     "updated_at": "2024-01-15T10:30:00"
#   }
# }


# 2. INICIAR SESIÓN
POST http://localhost:8000/api/v1/users/login
Content-Type: application/json

{
  "username": "nuevo_usuario",
  "password": "password123"
}

# Respuesta exitosa:
# {
#   "success": true,
#   "message": "Autenticación exitosa",
#   "data": {
#     "access_token": "eyJhbGc...",
#     "refresh_token": "eyJhbGc...",
#     "token_type": "bearer",
#     "expires_in": 1800
#   }
# }


# ============================
# USUARIO ACTUAL
# ============================

# 3. OBTENER INFORMACIÓN DEL USUARIO ACTUAL
GET http://localhost:8000/api/v1/users/me
Authorization: Bearer <token>


# 4. ACTUALIZAR INFORMACIÓN DEL USUARIO
PUT http://localhost:8000/api/v1/users/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "nuevo_email@restaurant.com",
  "full_name": "Nombre Actualizado",
  "phone": "9876543210",
  "is_active": true
}


# ============================
# ADMINISTRACIÓN DE USUARIOS (ADMIN ONLY)
# ============================

# 5. LISTAR TODOS LOS USUARIOS
GET http://localhost:8000/api/v1/users?skip=0&limit=10
Authorization: Bearer <admin_token>


# 6. OBTENER USUARIO ESPECÍFICO
GET http://localhost:8000/api/v1/users/1
Authorization: Bearer <admin_token>


# 7. LISTAR USUARIOS POR ROL
GET http://localhost:8000/api/v1/users/role/CAMARERO?skip=0&limit=10
Authorization: Bearer <admin_token>


# 8. ELIMINAR USUARIO
DELETE http://localhost:8000/api/v1/users/1
Authorization: Bearer <admin_token>


# ============================
# GESTIÓN DE MESAS (ADMIN)
# ============================

# 9. CREAR NUEVA MESA
POST http://localhost:8000/api/v1/tables
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "table_number": 11,
  "capacity": 4,
  "location": "Sección C - Cerca de la ventana"
}


# 10. OBTENER MESA ESPECÍFICA
GET http://localhost:8000/api/v1/tables/1
Authorization: Bearer <token>


# 11. LISTAR TODAS LAS MESAS
GET http://localhost:8000/api/v1/tables?skip=0&limit=10
Authorization: Bearer <token>


# 12. OBTENER MESA POR NÚMERO
GET http://localhost:8000/api/v1/tables/number/5
Authorization: Bearer <token>


# 13. OBTENER MESAS DISPONIBLES
GET http://localhost:8000/api/v1/tables/available/list?skip=0&limit=10
Authorization: Bearer <token>


# 14. ACTUALIZAR MESA
PUT http://localhost:8000/api/v1/tables/1
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "capacity": 6,
  "status": "OCUPADA",
  "location": "Sección A - Cerca de la barra"
}


# 15. ELIMINAR MESA
DELETE http://localhost:8000/api/v1/tables/1
Authorization: Bearer <admin_token>


# ============================
# GESTIÓN DE PLATOS (ADMIN)
# ============================

# 16. CREAR NUEVO PLATO
POST http://localhost:8000/api/v1/dishes
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Carne asada premium",
  "description": "Carne de res de alta calidad asada a la parrilla",
  "price": 1500,
  "estimated_time": 1200,
  "category": "Platos Principales",
  "preparation_notes": "Punto medio-alto"
}


# 17. OBTENER PLATO ESPECÍFICO
GET http://localhost:8000/api/v1/dishes/1
Authorization: Bearer <token>


# 18. LISTAR TODOS LOS PLATOS
GET http://localhost:8000/api/v1/dishes?skip=0&limit=10
Authorization: Bearer <token>


# 19. OBTENER PLATOS POR CATEGORÍA
GET http://localhost:8000/api/v1/dishes/category/Platos%20Principales?skip=0&limit=10
Authorization: Bearer <token>


# 20. BUSCAR PLATOS
GET http://localhost:8000/api/v1/dishes/search/query?query=asada&skip=0&limit=10
Authorization: Bearer <token>


# 21. OBTENER PLATOS DISPONIBLES
GET http://localhost:8000/api/v1/dishes/available/list?skip=0&limit=10
Authorization: Bearer <token>


# 22. ACTUALIZAR PLATO
PUT http://localhost:8000/api/v1/dishes/1
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Carne asada premium deluxe",
  "price": 1600,
  "estimated_time": 1200,
  "is_available": true,
  "preparation_notes": "Punto medio, bien sazonada"
}


# 23. ELIMINAR PLATO
DELETE http://localhost:8000/api/v1/dishes/1
Authorization: Bearer <admin_token>


# ============================
# GESTIÓN DE PEDIDOS
# ============================

# 24. CREAR NUEVO PEDIDO (CAMARERO)
POST http://localhost:8000/api/v1/orders
Authorization: Bearer <camarero_token>
Content-Type: application/json

{
  "table_id": 1,
  "items": [
    {
      "dish_id": 3,
      "quantity": 2,
      "special_notes": "Sin picante"
    },
    {
      "dish_id": 5,
      "quantity": 1,
      "special_notes": "Con jugo de limón extra"
    }
  ],
  "notes": "Cliente es VIP, atención especial"
}

# Respuesta:
# {
#   "success": true,
#   "message": "Pedido creado exitosamente",
#   "data": {
#     "id": 1,
#     "table_id": 1,
#     "camarero_id": 2,
#     "status": "NUEVO",
#     "total_amount": 4200,
#     "notes": "Cliente es VIP, atención especial",
#     "items": [
#       {
#         "id": 1,
#         "order_id": 1,
#         "dish_id": 3,
#         "quantity": 2,
#         "unit_price": 1200,
#         "status": "PENDIENTE",
#         "special_notes": "Sin picante",
#         "started_at": null,
#         "completed_at": null,
#         "created_at": "2024-01-15T10:30:00",
#         "updated_at": "2024-01-15T10:30:00"
#       },
#       {
#         "id": 2,
#         "order_id": 1,
#         "dish_id": 5,
#         "quantity": 1,
#         "unit_price": 1400,
#         "status": "PENDIENTE",
#         "special_notes": "Con jugo de limón extra",
#         "started_at": null,
#         "completed_at": null,
#         "created_at": "2024-01-15T10:30:00",
#         "updated_at": "2024-01-15T10:30:00"
#       }
#     ],
#     "started_at": null,
#     "completed_at": null,
#     "delivered_at": null,
#     "created_at": "2024-01-15T10:30:00",
#     "updated_at": "2024-01-15T10:30:00"
#   }
# }


# 25. OBTENER PEDIDO ESPECÍFICO
GET http://localhost:8000/api/v1/orders/1
Authorization: Bearer <token>


# 26. LISTAR TODOS LOS PEDIDOS
GET http://localhost:8000/api/v1/orders?skip=0&limit=10
Authorization: Bearer <token>


# 27. OBTENER PEDIDO ACTIVO DE UNA MESA
GET http://localhost:8000/api/v1/orders/table/1/active
Authorization: Bearer <token>


# 28. OBTENER PEDIDOS POR ESTADO
GET http://localhost:8000/api/v1/orders/status/EN_COCINA?skip=0&limit=10
Authorization: Bearer <token>


# 29. ACTUALIZAR ESTADO DEL PEDIDO
PUT http://localhost:8000/api/v1/orders/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "EN_COCINA",
  "notes": "Pedido enviado a cocina"
}


# 30. ACTUALIZAR ESTADO DE ITEM DE PEDIDO (COCINERO)
PUT http://localhost:8000/api/v1/orders/items/1
Authorization: Bearer <cocinero_token>
Content-Type: application/json

{
  "status": "EN_PREPARACION"
}

# Posteriormente:
PUT http://localhost:8000/api/v1/orders/items/1
Authorization: Bearer <cocinero_token>
Content-Type: application/json

{
  "status": "LISTO"
}


# 31. ELIMINAR PEDIDO (ADMIN)
DELETE http://localhost:8000/api/v1/orders/1
Authorization: Bearer <admin_token>


# ============================
# NOTIFICACIONES
# ============================

# 32. OBTENER NOTIFICACIÓN ESPECÍFICA
GET http://localhost:8000/api/v1/notifications/1
Authorization: Bearer <token>


# 33. OBTENER NOTIFICACIONES DE UN PEDIDO
GET http://localhost:8000/api/v1/notifications/order/1
Authorization: Bearer <token>


# 34. OBTENER NOTIFICACIONES SIN LEER (PARA MI ROL)
GET http://localhost:8000/api/v1/notifications/unread?skip=0&limit=10
Authorization: Bearer <token>


# 35. MARCAR NOTIFICACIÓN COMO LEÍDA
PUT http://localhost:8000/api/v1/notifications/1/read
Authorization: Bearer <token>


# ============================
# FLUJO COMPLETO DE EJEMPLO
# ============================

# PASO 1: Camarero toma pedido en mesa 3
POST http://localhost:8000/api/v1/orders
Authorization: Bearer <camarero_token>
{
  "table_id": 3,
  "items": [
    {"dish_id": 1, "quantity": 1, "special_notes": ""},
    {"dish_id": 5, "quantity": 2, "special_notes": ""}
  ],
  "notes": ""
}
# Resultado: order_id = 1


# PASO 2: Cocinero ve notificación de nuevo pedido
GET http://localhost:8000/api/v1/notifications/unread
Authorization: Bearer <cocinero_token>


# PASO 3: Cocinero comienza preparación
PUT http://localhost:8000/api/v1/orders/items/1
Authorization: Bearer <cocinero_token>
{"status": "EN_PREPARACION"}


# PASO 4: Cocinero termina primer item
PUT http://localhost:8000/api/v1/orders/items/1
Authorization: Bearer <cocinero_token>
{"status": "LISTO"}


# PASO 5: Camarero ve notificación de plato listo
GET http://localhost:8000/api/v1/notifications/unread
Authorization: Bearer <camarero_token>


# PASO 6: Camarero marca notificación como leída
PUT http://localhost:8000/api/v1/notifications/1/read
Authorization: Bearer <camarero_token>


# PASO 7: Camarero entrega pedido completamente
PUT http://localhost:8000/api/v1/orders/1
Authorization: Bearer <camarero_token>
{"status": "ENTREGADO"}


# ============================
# FILTROS Y BÚSQUEDA
# ============================

# Parámetros disponibles en la mayoría de endpoints:
# - skip: número de registros a saltar (por defecto 0)
# - limit: número máximo de registros a retornar (por defecto 10, máximo 100)

GET http://localhost:8000/api/v1/orders?skip=10&limit=20
Authorization: Bearer <token>

# Búsqueda de platos:
GET http://localhost:8000/api/v1/dishes/search/query?query=pollo&skip=0&limit=10
Authorization: Bearer <token>

# ============================
# CÓDIGOS DE ESTADO HTTP
# ============================

# 200 OK - Solicitud exitosa
# 201 CREATED - Recurso creado exitosamente
# 204 NO CONTENT - Operación exitosa (sin contenido en respuesta)
# 400 BAD REQUEST - Solicitud inválida
# 401 UNAUTHORIZED - Autenticación requerida
# 403 FORBIDDEN - No tiene permisos
# 404 NOT FOUND - Recurso no encontrado
# 422 UNPROCESSABLE ENTITY - Validación fallida
# 500 INTERNAL SERVER ERROR - Error del servidor

# ============================
# NOTAS
# ============================

# 1. Reemplaza <token>, <admin_token>, <camarero_token>, <cocinero_token> con tokens reales
# 2. Los precios se almacenan en centavos (1500 = $15.00)
# 3. Los tiempos se almacenan en segundos (1200 = 20 minutos)
# 4. Los estados son fijos: NUEVO, EN_COCINA, COMPLETADO, ENTREGADO, CANCELADO
# 5. Los roles son: ADMIN, COCINERO, CAMARERO
# 6. Los cambios de estado generan automáticamente notificaciones
