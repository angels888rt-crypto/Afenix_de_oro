"""
GUÍA DE INSTALACIÓN Y EJECUCIÓN
Restaurant Order Management API
"""

## REQUISITOS PREVIOS

- Python 3.12 o superior
- MySQL 8.0 o superior
- pip (incluido con Python)

## INSTALACIÓN PASO A PASO

### 1. Crear Base de Datos MySQL

Ejecuta estos comandos en MySQL:

```sql
CREATE DATABASE restaurant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'restaurant_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON restaurant_db.* TO 'restaurant_user'@'localhost';
FLUSH PRIVILEGES;
```

Alternativamente, si usas root sin contraseña:
```sql
CREATE DATABASE restaurant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Clonar/Preparar el Proyecto

```bash
cd path/to/project
```

### 3. Crear Entorno Virtual

#### En Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### En Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### En Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar Variables de Entorno

Copiar archivo de ejemplo:
```bash
copy .env.example .env
```

Editar `.env` con tu editor de texto:
```env
APP_NAME=Restaurant Order Management System
APP_VERSION=1.0.0
APP_ENV=development
DEBUG=True

# Tu configuración MySQL
DB_HOST=localhost
DB_PORT=3306
DB_NAME=restaurant_db
DB_USER=restaurant_user
DB_PASSWORD=secure_password
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# JWT (puedes dejar los valores por defecto para desarrollo)
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
RELOAD=True

CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### 6. Ejecutar Migraciones

```bash
alembic upgrade head
```

### 7. Inicializar Datos de Demostración (Opcional)

```bash
python init_demo_data.py
```

Esto crea:
- 1 usuario admin (usuario: admin, contraseña: admin123)
- 2 cocineros
- 2 camareros
- 10 mesas
- 12 platos en el menú

### 8. Iniciar el Servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: http://localhost:8000

## ACCESO A LA API

### Documentación Interactiva

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Endpoint de Prueba

```bash
curl http://localhost:8000/health
```

## PRIMEROS PASOS CON LA API

### 1. Registrar un Nuevo Usuario

```bash
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nuevo_camarero",
    "email": "camarero@restaurant.com",
    "password": "password123",
    "full_name": "Nombre Completo",
    "role": "CAMARERO",
    "phone": "1234567890"
  }'
```

### 2. Iniciar Sesión

```bash
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nuevo_camarero",
    "password": "password123"
  }'
```

Guarda el `access_token` que recibas para el siguiente paso.

### 3. Obtener tu Información de Usuario

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <tu_access_token>"
```

### 4. Crear un Pedido

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer <tu_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "table_id": 1,
    "items": [
      {
        "dish_id": 1,
        "quantity": 2,
        "special_notes": "Sin picante"
      },
      {
        "dish_id": 3,
        "quantity": 1,
        "special_notes": ""
      }
    ],
    "notes": "Cliente tiene prisa"
  }'
```

### 5. Ver Platos Disponibles

```bash
curl -X GET "http://localhost:8000/api/v1/dishes/available/list" \
  -H "Authorization: Bearer <tu_access_token>"
```

## FLUJO DE NEGOCIO COMPLETO

### Para Camareros (CAMARERO)

1. **Tomar pedido en mesa:**
   - POST /api/v1/orders (crear nuevo pedido)
   
2. **Ver pedidos activos:**
   - GET /api/v1/orders/table/{table_id}/active
   
3. **Ver notificaciones de platos listos:**
   - GET /api/v1/notifications/unread
   
4. **Marcar notificaciones como leídas:**
   - PUT /api/v1/notifications/{notification_id}/read
   
5. **Entregar pedido:**
   - PUT /api/v1/orders/{order_id} (cambiar estado a ENTREGADO)

### Para Cocineros (COCINERO)

1. **Ver notificaciones de nuevos pedidos:**
   - GET /api/v1/notifications/unread
   
2. **Ver pedidos en cocina:**
   - GET /api/v1/orders/status/NUEVO
   - GET /api/v1/orders/status/EN_COCINA
   
3. **Iniciar preparación de plato:**
   - PUT /api/v1/orders/items/{item_id} (cambiar estado a EN_PREPARACION)
   
4. **Marcar plato como listo:**
   - PUT /api/v1/orders/items/{item_id} (cambiar estado a LISTO)

### Para Administradores (ADMIN)

1. **Crear mesas:**
   - POST /api/v1/tables
   
2. **Agregar platos al menú:**
   - POST /api/v1/dishes
   
3. **Crear usuarios:**
   - POST /api/v1/users/register
   
4. **Ver reportes:**
   - GET /api/v1/orders
   - GET /api/v1/orders/status/{status}

## SOLUCIÓN DE PROBLEMAS

### Error: "No such module named 'app'"

Asegúrate de:
- Estás en el directorio correcto (donde está `main.py`)
- El entorno virtual está activado
- Has ejecutado `pip install -r requirements.txt`

### Error: "MySQL Server has gone away"

- Verifica que MySQL está corriendo
- Revisa las credenciales en `.env`
- Verifica que la base de datos existe

### Error: "CORS error"

- Asegúrate de que CORS_ORIGINS en `.env` incluya tu frontend
- Por defecto está configurado para http://localhost:3000 y http://localhost:8000

### Error: "Token invalido"

- El token ha expirado (configurado para 30 minutos por defecto)
- Haz login nuevamente para obtener un nuevo token

## DEPLOYMENT EN PRODUCCIÓN

Para un ambiente de producción:

1. **Cambiar variables en `.env`:**
   ```env
   APP_ENV=production
   DEBUG=False
   JWT_SECRET=<generar-clave-segura>
   RELOAD=False
   ```

2. **Usar Gunicorn:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 main:app
   ```

3. **Usar Nginx como reverse proxy**

4. **Configurar HTTPS/SSL**

5. **Configurar variables CORS adecuadas**

## ESTRUCTURA DEL PROYECTO

```
project/
├── app/
│   ├── domain/                  # Lógica de negocio pura
│   ├── application/             # Casos de uso
│   ├── infrastructure/          # Base de datos, seguridad
│   ├── presentation/            # API REST
│   └── shared/                  # Excepciones, respuestas
├── alembic/                     # Migraciones de BD
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias
├── init_demo_data.py           # Script para datos de demo
├── .env.example                 # Variables de ejemplo
└── README.md                    # Documentación
```

## CONTACTO Y SOPORTE

Para problemas o consultas, consulta la documentación completa en README.md

¡Disfruta usando la API!
