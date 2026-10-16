"""
ARCHITECTURE.md - Explicación de la Arquitectura Clean Architecture

## VISIÓN GENERAL

Este proyecto implementa Clean Architecture (también conocida como Hexagonal Architecture)
dividiendo la lógica en capas independientes y desacopladas.

## CAPAS DE LA ARQUITECTURA

### 1. CAPA DE DOMINIO (Domain Layer)
**Ubicación:** app/domain/

**Responsabilidades:**
- Contiene la lógica de negocio pura, independiente de cualquier framework
- Define las entidades de negocio como dataclasses
- Define interfaces (contratos) para repositorios y servicios

**Archivos principales:**
- `entities/__init__.py` - Entidades: User, Table, Dish, Order, OrderItem, Notification
- `repositories/__init__.py` - Interfaces de repositorios (IRepository, IUserRepository, etc.)
- `services/__init__.py` - Servicios de dominio: OrderService, OrderItemService, NotificationService

**Características:**
- Independiente de cualquier framework de web
- Independiente de la base de datos
- Fácil de testear

**Ejemplo:**
```python
@dataclass
class Order:
    id: Optional[int] = None
    table_id: int = None
    camarero_id: Optional[int] = None
    status: str = OrderStatus.NUEVO.value
    total_amount: int = 0
    ...
```


### 2. CAPA DE APLICACIÓN (Application Layer)
**Ubicación:** app/application/

**Responsabilidades:**
- Contiene los Casos de Uso (Use Cases) que orquestan la lógica de negocio
- Contiene los DTOs (Data Transfer Objects) para validación y serialización
- Orquesta llamadas a repositorios y servicios de dominio

**Archivos principales:**
- `use_cases/` - Contiene todos los casos de uso organizados por dominio:
  - `user_use_cases.py` - RegisterUserUseCase, LoginUserUseCase, etc.
  - `table_use_cases.py` - CreateTableUseCase, ListTablesUseCase, etc.
  - `dish_use_cases.py` - CreateDishUseCase, SearchDishesUseCase, etc.
  - `order_use_cases.py` - CreateOrderUseCase, UpdateOrderStatusUseCase, etc.
  - `notification_use_cases.py` - GetNotificationUseCase, MarkAsReadUseCase, etc.

- `dto/__init__.py` - Data Transfer Objects con validación Pydantic v2:
  - Requests: UserRegisterRequest, TableCreateRequest, OrderCreateRequest, etc.
  - Responses: UserResponse, TableResponse, OrderDetailResponse, etc.
  - Schemas: TokenResponse, PaginationParams, PaginatedResponse[T]

**Características:**
- Cada caso de uso es una clase con método `async execute()`
- Validación de reglas de negocio
- Manejo de transacciones
- Mapeo entre DTOs y entidades de dominio

**Ejemplo:**
```python
class CreateOrderUseCase:
    async def execute(self, request: OrderCreateRequest, user_id: int) -> Order:
        # Validar que la mesa exista y esté disponible
        # Validar que los platos existan y estén disponibles
        # Calcular el total
        # Crear el pedido
        # Crear notificaciones
        # Retornar la entidad Order
        pass
```


### 3. CAPA DE INFRAESTRUCTURA (Infrastructure Layer)
**Ubicación:** app/infrastructure/

**Responsabilidades:**
- Implementación técnica de bases de datos, seguridad, configuración
- Implementa los interfaces definidos en la capa de dominio
- Gestiona la comunicación con sistemas externos

**Subcapas:**

#### a. Configuration (config/)
- `settings.py` - Gestión de variables de entorno con Pydantic BaseSettings
- Database URLs, JWT secrets, CORS origins, etc.

#### b. Database (database/)
- `models/database_models.py` - Modelos SQLAlchemy 2.0
- `session.py` - Gestión de sesiones async con AsyncSessionLocal
- `repositories/` - Implementación concreta de repositorios:
  - `base_repositories.py` - UserRepository, TableRepository, DishRepository
  - `order_repositories.py` - OrderRepository, OrderItemRepository, NotificationRepository

#### c. Security (security/)
- `jwt_handler.py` - Token JWT, password hashing, verificación

**Características:**
- Desacoplada del dominio mediante interfaces
- Fácil de cambiar de tecnología (ej: cambiar SQLAlchemy por otra ORM)
- Implementa el patrón Repository


### 4. CAPA DE PRESENTACIÓN (Presentation Layer)
**Ubicación:** app/presentation/

**Responsabilidades:**
- Define los endpoints HTTP de la API REST
- Valida solicitudes HTTP
- Convierte respuestas a formato HTTP

**Archivos principales:**
- `api/routers/` - Routers de FastAPI:
  - `user_router.py` - Endpoints de usuario (/users/*)
  - `table_router.py` - Endpoints de mesas (/tables/*)
  - `dish_router.py` - Endpoints de platos (/dishes/*)
  - `order_router.py` - Endpoints de pedidos (/orders/*)
  - `notification_router.py` - Endpoints de notificaciones (/notifications/*)

- `api/dependencies/auth_dependencies.py` - Inyección de dependencias y autenticación:
  - `get_current_user()` - Extrae el usuario del JWT
  - `require_role()` - Verifica permisos por rol
  - Funciones para obtener repositorios

- `api/middleware/exception_handlers.py` - Manejo de excepciones global

**Características:**
- Endpoints RESTful
- Manejo automático de excepciones
- Validación con Pydantic
- Respuestas estandarizadas

**Ejemplo:**
```python
@router.post("/", response_model=ResponseSchema[OrderDetailResponse])
async def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    use_case = CreateOrderUseCase(order_repo)
    result = await use_case.execute(request, current_user.id)
    return ResponseSchema(success=True, data=result)
```


### 5. CAPA COMPARTIDA (Shared Layer)
**Ubicación:** app/shared/

**Responsabilidades:**
- Código compartido entre capas
- Excepciones personalizadas
- Esquemas de respuesta
- Constantes y enumeraciones

**Archivos principales:**
- `exceptions/custom_exceptions.py` - Excepciones personalizadas
- `responses/response_schema.py` - Esquemas estandarizados de respuesta
- `constants/enums.py` - Enumeraciones: UserRole, OrderStatus, etc.

**Características:**
- Respuestas consistentes
- Errores bien estructurados
- Tipos seguros con Enum


## FLUJO DE DATOS

```
HTTP Request
    ↓
FastAPI Endpoint (presentation/api/routers/)
    ↓
Dependency Injection (get_current_user, get_*_repository)
    ↓
Use Case (application/use_cases/)
    ↓
Domain Services (domain/services/)
    ↓
Repository Pattern (infrastructure/database/repositories/)
    ↓
SQLAlchemy Database Models (infrastructure/database/models/)
    ↓
MySQL Database
    ↓
Repository (retorna Domain Entity)
    ↓
Use Case (mapea a DTO)
    ↓
Endpoint (retorna ResponseSchema)
    ↓
HTTP Response
```


## PATRONES IMPLEMENTADOS

### 1. Repository Pattern
- Interface: `app/domain/repositories/`
- Implementación: `app/infrastructure/database/repositories/`
- Beneficio: Desacopla acceso a datos de lógica de negocio

### 2. Use Cases Pattern
- Ubicación: `app/application/use_cases/`
- Beneficio: Cada caso de uso es una clase reutilizable

### 3. Dependency Injection
- Framework: FastAPI Depends
- Ubicación: `app/presentation/api/dependencies/`
- Beneficio: Facilita testing y permite swapping de implementaciones

### 4. Data Transfer Objects (DTOs)
- Ubicación: `app/application/dto/`
- Beneficio: Validación automática con Pydantic, separación de concerns

### 5. Exception Handling
- Ubicación: `app/shared/exceptions/` y `app/presentation/api/middleware/`
- Beneficio: Errores consistentes y bien estructurados

### 6. RBAC (Role-Based Access Control)
- Ubicación: `app/presentation/api/dependencies/auth_dependencies.py`
- Implementación: `require_role()` como middleware
- Roles: ADMIN, COCINERO, CAMARERO


## VENTAJAS DE ESTA ARQUITECTURA

1. **Testabilidad**: Cada capa puede testearse independientemente
2. **Flexibilidad**: Fácil cambiar implementaciones (ej: base de datos)
3. **Mantenibilidad**: Código organizado y separación de responsabilidades
4. **Escalabilidad**: Fácil agregar nuevas features
5. **Independencia de Frameworks**: La lógica de negocio no depende de FastAPI
6. **Reutilización**: Los casos de uso pueden usarse en CLI, workers, etc.


## ADICIÓN DE UNA NUEVA CARACTERÍSTICA

Para agregar una nueva característica (ej: Reviews de platos):

1. **Domain Layer**:
   - Crear entidad Review en `app/domain/entities/__init__.py`
   - Crear interfaz IReviewRepository en `app/domain/repositories/__init__.py`

2. **Application Layer**:
   - Crear DTOs en `app/application/dto/__init__.py`
   - Crear casos de uso en `app/application/use_cases/review_use_cases.py`

3. **Infrastructure Layer**:
   - Crear modelo ReviewModel en `app/infrastructure/database/models/database_models.py`
   - Crear ReviewRepository en `app/infrastructure/database/repositories/base_repositories.py`
   - Crear migración Alembic en `alembic/versions/002_add_reviews_table.py`

4. **Presentation Layer**:
   - Crear router en `app/presentation/api/routers/review_router.py`
   - Incluir router en `main.py`

5. **Tests**:
   - Agregar tests en `test_api.py`


## CONVENCIONES DE CÓDIGO

1. **Nombres de Archivos**: snake_case (user_repository.py)
2. **Nombres de Clases**: PascalCase (UserRepository)
3. **Nombres de Variables**: snake_case (user_id)
4. **Nombres de Funciones**: snake_case (get_user)
5. **Type Hints**: Siempre usar type hints
6. **Docstrings**: En todas las clases y funciones públicas


## EJEMPLO: CREAR UN PLATO

### 1. Request del Cliente
```
POST /api/v1/dishes
Authorization: Bearer <admin_token>
{
  "name": "Carne asada",
  "price": 1200,
  "estimated_time": 1200,
  "category": "Platos Principales"
}
```

### 2. Entrada en Endpoint (presentation/api/routers/dish_router.py)
```python
@router.post("/", response_model=ResponseSchema[DishResponse])
async def create_dish(
    request: DishCreateRequest,
    current_user: User = Depends(get_current_user),
    dish_repo: DishRepository = Depends(get_dish_repository)
):
    # Validar que sea admin
    # Crear uso caso
    # Ejecutar
    # Retornar respuesta
```

### 3. Validación con Pydantic (application/dto/)
```python
class DishCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    price: int = Field(..., gt=0)
    estimated_time: int = Field(..., gt=0)
    category: str = Field(..., min_length=3, max_length=50)
```

### 4. Ejecución del Caso de Uso (application/use_cases/dish_use_cases.py)
```python
class CreateDishUseCase:
    async def execute(self, request: DishCreateRequest) -> Dish:
        # Validar que el plato no exista
        # Crear la entidad Dish
        # Guardar en repositorio
        # Retornar entidad Dish
```

### 5. Mapeo a Modelo de BD (infrastructure/database/repositories/)
```python
class DishRepository(IRepository[Dish]):
    async def create(self, entity: Dish) -> Dish:
        # Mapear Dish → DishModel
        # Guardar en BD
        # Mapear DishModel → Dish
        # Retornar
```

### 6. Almacenamiento en BD (MySQL)
```sql
INSERT INTO dishes (name, price, estimated_time, category, ...)
VALUES ('Carne asada', 1200, 1200, 'Platos Principales', ...)
```

### 7. Respuesta al Cliente
```json
{
  "success": true,
  "message": "Plato creado exitosamente",
  "data": {
    "id": 1,
    "name": "Carne asada",
    "price": 1200,
    "estimated_time": 1200,
    "category": "Platos Principales",
    "created_at": "2024-01-15T10:30:00"
  }
}
```


## DOCUMENTACIÓN ADICIONAL

- INSTALL.md - Instrucciones de instalación
- EXAMPLES.md - Ejemplos de uso de la API
- README.md - Documentación completa del proyecto

"""
