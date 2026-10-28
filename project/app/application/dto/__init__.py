"""Generic type for DTOs."""
from typing import TypeVar, Generic

T = TypeVar("T")
"""Generic type for DTOs."""
from typing import TypeVar, Generic, Optional
from datetime import datetime

from typing import Optional, Union
from datetime import datetime

from pydantic import BaseModel, Field

T = TypeVar("T")


# ==================== User DTOs ====================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=3, max_length=100)
    role: str = Field(default="CAMARERO", pattern="^(ADMIN|CAMARERO|CAJERO|MONITOR)$")
    phone: Optional[str] = Field(None, max_length=20)


class UserLoginRequest(BaseModel):
    """User login request."""
    username: str = Field(...)
    password: str = Field(...)
    role: Optional[str] = Field(None, pattern="^(ADMIN|CAMARERO|CAJERO|MONITOR)$")


class UserResponse(BaseModel):
    """User response."""
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseModel):
    """User update request."""
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class AdminUserUpdateRequest(BaseModel):
    """Admin-level user update request."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    role: Optional[str] = Field(None, pattern="^(ADMIN|CAMARERO|CAJERO|MONITOR)$")
    is_active: Optional[bool] = None
    phone: Optional[str] = Field(None, max_length=20)


# ==================== Authentication DTOs ====================

class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    display_name: Optional[str] = None
    role: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# ==================== Table DTOs ====================

class TableCreateRequest(BaseModel):
    """Table creation request."""
    table_number: int = Field(..., gt=0)
    capacity: int = Field(..., gt=0)
    location: Optional[str] = Field(None, max_length=100)


class TableUpdateRequest(BaseModel):
    """Table update request."""
    capacity: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(DISPONIBLE|OCUPADA|RESERVADA)$")
    location: Optional[str] = Field(None, max_length=100)


class TableResponse(BaseModel):
    """Table response."""
    id: int
    table_number: int
    capacity: int
    status: str
    location: Optional[str]
    created_at: datetime
    updated_at: datetime


# ==================== Dish DTOs ====================

class DishCreateRequest(BaseModel):
    """Dish creation request."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    price: int = Field(..., gt=0)  # In cents
    estimated_time: int = Field(..., gt=0)  # In seconds
    category: str = Field(..., min_length=3, max_length=50)
    is_available: bool = Field(default=True)
    preparation_notes: Optional[str] = None


class DishUpdateRequest(BaseModel):
    """Dish update request."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    price: Optional[int] = Field(None, gt=0)
    estimated_time: Optional[int] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=3, max_length=50)
    is_available: Optional[bool] = None
    preparation_notes: Optional[str] = None


class DishResponse(BaseModel):
    """Dish response."""
    id: int
    name: str
    description: Optional[str] = None
    price: int
    estimated_time: int
    category: str
    is_available: bool
    preparation_notes: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==================== Order Item DTOs ====================

class OrderItemCreateRequest(BaseModel):
    """Order item creation request."""
    dish_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    special_notes: Optional[str] = None


class OrderItemUpdateRequest(BaseModel):
    """Order item update request."""
    quantity: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(PENDIENTE|EN_PREPARACION|LISTO|ENTREGADO|CANCELADO)$")
    special_notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Order item response with the dish name for user-facing order screens."""
    id: int
    order_id: int
    dish_id: int
    dish_name: Optional[str] = None
    quantity: int
    unit_price: int
    status: str
    special_notes: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ==================== Order DTOs ====================

class OrderCreateRequest(BaseModel):
    """Order creation request. A waiter may identify a table by its number."""
    table_id: Optional[int] = Field(None, gt=0)
    table_number: Optional[int] = Field(None, gt=0)
    items: list[OrderItemCreateRequest] = Field(..., min_length=1)
    notes: Optional[str] = None


class OrderUpdateRequest(BaseModel):
    """Order update request."""
    status: Optional[str] = Field(None, pattern="^(PENDIENTE|NUEVO|EN_COCINA|COMPLETADO|ENTREGADO|CANCELADO|PAGADO)$")
    notes: Optional[str] = None


class OrderEditRequest(BaseModel):
    """Request for mesero to edit pending order items."""
    items: list[OrderItemCreateRequest] = Field(..., min_length=1)
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response."""
    id: int
    table_id: int
    table_number: Optional[int] = None
    camarero_id: Optional[int]
    camarero_name: Optional[str] = None
    status: str
    total_amount: int
    notes: Optional[str]
    items: list[OrderItemResponse]
    daily_number: Optional[int] = None
    cycle_key: Optional[str] = None
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    delivered_at: Optional[datetime]
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OrderDetailResponse(OrderResponse):
    """Order detail response with additional information."""
    camarero_name: Optional[str] = None
    table_number: Optional[int] = None
    table_capacity: Optional[int] = None


# ==================== Notification DTOs ====================

class NotificationResponse(BaseModel):
    """Notification response."""
    id: int
    order_id: int
    event_type: str
    target_role: str
    message: str
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime


# ==================== History DTOs ====================

class HistoryResponse(BaseModel):
    """History log response."""
    id: int
    category: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    description: str
    details: Optional[dict] = None
    performed_by: Optional[int] = None
    performed_by_username: Optional[str] = None
    created_at: datetime


# ==================== Receipt Config DTOs ====================

class ReceiptConfigResponse(BaseModel):
    """Receipt config response."""
    id: int
    restaurant_name: str
    footer_message: str
    logo_path: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None


class ReceiptConfigUpdateRequest(BaseModel):
    """Receipt config update request."""
    restaurant_name: Optional[str] = Field(None, min_length=1, max_length=100)
    footer_message: Optional[str] = Field(None, max_length=500)
    logo_path: Optional[str] = Field(None, max_length=255)


# ==================== Pagination DTOs ====================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool


# ==================== Category DTOs ====================

class CategoryCreateRequest(BaseModel):
    """Category creation request."""
    name: str = Field(..., min_length=2, max_length=80)
    description: Optional[str] = Field(None, max_length=200)


class CategoryUpdateRequest(BaseModel):
    """Category update request."""
    name: str = Field(..., min_length=2, max_length=80)
    description: Optional[str] = Field(None, max_length=200)


class CategoryResponse(BaseModel):
    """Category response."""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
