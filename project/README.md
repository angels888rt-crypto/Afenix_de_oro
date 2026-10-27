"""
Restaurant Order Management API

A professional REST API for managing orders in restaurants.
Solves communication issues between waiters and kitchen staff.

Built with:
- FastAPI
- SQLAlchemy 2.0
- MySQL
- Pydantic v2
- JWT Authentication
- Clean Architecture

## Quick Start

1. Create virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. Initialize database:
   ```
   alembic upgrade head
   ```

5. Run the server:
   ```
   uvicorn main:app --reload
   python -m uvicorn main:app --reload
   ```

The API will be available at http://localhost:8000
API documentation available at http://localhost:8000/api/docs

## Architecture

```
project/
├── app/
│   ├── domain/              # Business logic (entities, repositories, services)
│   ├── application/         # Use cases, DTOs
│   ├── infrastructure/      # Database, security, configuration
│   ├── presentation/        # API routers, dependencies, middleware
│   └── shared/              # Exceptions, responses, constants, utils
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

## Key Features

- **Authentication**: JWT with access and refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Order Management**: Complete order lifecycle tracking
- **Real-time Notifications**: System for kitchen and waiter notifications
- **Clean Architecture**: Separation of concerns, dependency injection
- **API Documentation**: Auto-generated Swagger/OpenAPI docs
- **Database Migrations**: Alembic for version control
- **Soft Deletes**: Audit trail with created_at, updated_at, deleted_at

## Database Schema

### Users
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- full_name
- role (ADMIN, COCINERO, CAMARERO)
- is_active
- phone
- Timestamps and audit fields

### Tables
- id (Primary Key)
- table_number (Unique)
- capacity
- status (DISPONIBLE, OCUPADA, RESERVADA)
- location
- Timestamps and audit fields

### Dishes
- id (Primary Key)
- name
- description
- price (in cents)
- estimated_time (in seconds)
- category
- is_available
- preparation_notes
- Timestamps and audit fields

### Orders
- id (Primary Key)
- table_id (Foreign Key)
- camarero_id (Foreign Key to Users)
- status (NUEVO, EN_COCINA, COMPLETADO, ENTREGADO, CANCELADO)
- total_amount (in cents)
- notes
- started_at, completed_at, delivered_at
- Timestamps and audit fields

### Order Items
- id (Primary Key)
- order_id (Foreign Key)
- dish_id (Foreign Key)
- quantity
- unit_price (in cents)
- status (PENDIENTE, EN_PREPARACION, LISTO, ENTREGADO, CANCELADO)
- special_notes
- started_at, completed_at
- Timestamps and audit fields

### Notifications
- id (Primary Key)
- order_id (Foreign Key)
- event_type
- target_role
- message
- is_read
- read_at
- Timestamps and audit fields

## API Endpoints

### Users
- POST /api/v1/users/register - Register new user
- POST /api/v1/users/login - Login and get tokens
- GET /api/v1/users/me - Get current user
- GET /api/v1/users - List users (admin)
- GET /api/v1/users/{user_id} - Get user (admin)
- PUT /api/v1/users/{user_id} - Update user
- DELETE /api/v1/users/{user_id} - Delete user (admin)
- GET /api/v1/users/role/{role} - Get users by role (admin)

### Tables
- POST /api/v1/tables - Create table (admin)
- GET /api/v1/tables - List tables
- GET /api/v1/tables/{table_id} - Get table
- PUT /api/v1/tables/{table_id} - Update table (admin)
- DELETE /api/v1/tables/{table_id} - Delete table (admin)
- GET /api/v1/tables/available/list - Get available tables
- GET /api/v1/tables/number/{table_number} - Get table by number

### Dishes
- POST /api/v1/dishes - Create dish (admin)
- GET /api/v1/dishes - List dishes
- GET /api/v1/dishes/{dish_id} - Get dish
- PUT /api/v1/dishes/{dish_id} - Update dish (admin)
- DELETE /api/v1/dishes/{dish_id} - Delete dish (admin)
- GET /api/v1/dishes/category/{category} - Get dishes by category
- GET /api/v1/dishes/search/query?query=... - Search dishes
- GET /api/v1/dishes/available/list - Get available dishes

### Orders
- POST /api/v1/orders - Create order (camarero)
- GET /api/v1/orders - List orders
- GET /api/v1/orders/{order_id} - Get order
- PUT /api/v1/orders/{order_id} - Update order status
- DELETE /api/v1/orders/{order_id} - Delete order (admin)
- GET /api/v1/orders/status/{status} - Get orders by status
- GET /api/v1/orders/table/{table_id}/active - Get active order for table
- PUT /api/v1/orders/items/{item_id} - Update order item status (cocinero)

### Notifications
- GET /api/v1/notifications/{notification_id} - Get notification
- GET /api/v1/notifications/order/{order_id} - Get order notifications
- GET /api/v1/notifications/unread - Get unread notifications
- PUT /api/v1/notifications/{notification_id}/read - Mark as read

## Authentication

Include JWT token in request headers:
```
Authorization: Bearer <your_jwt_token>
```

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "errors": []
}
```

## Business Logic

### Order Workflow
1. Waiter (CAMARERO) creates order for table
2. System notifies kitchen (COCINERO)
3. Kitchen marks items as in preparation
4. Kitchen marks items as ready (notifies waiter)
5. Waiter delivers to table and marks order as delivered
6. System records all timestamps for analytics

### Notifications
- Kitchen receives notifications for new orders
- Waiters receive notifications when dishes are ready
- Both receive notifications when order is completed/delivered
- All notifications can be marked as read

## Environment Variables

```
APP_NAME=Restaurant Order Management System
APP_VERSION=1.0.0
APP_ENV=development
DEBUG=True

DB_HOST=localhost
DB_PORT=3306
DB_NAME=restaurant_db
DB_USER=root
DB_PASSWORD=your_password
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

SERVER_HOST=0.0.0.0
SERVER_PORT=8000
RELOAD=True

CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## Database Setup

### MySQL

```sql
CREATE DATABASE restaurant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'restaurant_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON restaurant_db.* TO 'restaurant_user'@'localhost';
FLUSH PRIVILEGES;
```

Then run migrations:
```bash
alembic upgrade head
```

## Testing Endpoints

### Register User
```bash
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "camarero1",
    "email": "camarero1@example.com",
    "password": "password123",
    "full_name": "Juan Pérez",
    "role": "CAMARERO",
    "phone": "1234567890"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "camarero1",
    "password": "password123"
  }'
```

### Create Order
```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "table_id": 1,
    "items": [
      {
        "dish_id": 1,
        "quantity": 2,
        "special_notes": "Sin picante"
      }
    ],
    "notes": "Cliente tiene prisa"
  }'
```

## Development

### Format Code
```bash
black .
```

### Lint
```bash
flake8 .
```

## Production Deployment

For production:
1. Set APP_ENV=production in .env
2. Set DEBUG=False
3. Change JWT_SECRET to a strong random value
4. Use a production ASGI server (Gunicorn + Uvicorn)
5. Use a reverse proxy (Nginx)
6. Enable HTTPS/SSL
7. Configure proper CORS origins

## License

MIT
"""
