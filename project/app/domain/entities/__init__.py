"""Domain entities."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.shared.constants.enums import UserRole, OrderStatus, OrderItemStatus, TableStatus


@dataclass
class User:
    """User domain entity."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: UserRole = UserRole.CAMARERO
    is_active: bool = True
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class Table:
    """Table domain entity."""
    id: Optional[int] = None
    table_number: int = 0
    capacity: int = 0
    status: TableStatus = TableStatus.DISPONIBLE
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class Dish:
    """Dish domain entity."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    price: int = 0  # In cents
    estimated_time: int = 0  # In seconds
    category: str = ""
    is_available: bool = True
    preparation_notes: Optional[str] = None
    image_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class OrderItem:
    """Order item domain entity."""
    id: Optional[int] = None
    order_id: Optional[int] = None
    dish_id: int = 0
    dish_name: Optional[str] = None
    quantity: int = 1
    unit_price: int = 0  # In cents
    status: OrderItemStatus = OrderItemStatus.PENDIENTE
    special_notes: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class Order:
    """Order domain entity."""
    id: Optional[int] = None
    table_id: int = 0
    table_number: Optional[int] = None  # Número visible de mesa (table.table_number)
    camarero_id: Optional[int] = None
    status: OrderStatus = OrderStatus.NUEVO
    total_amount: int = 0  # In cents
    notes: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None  # Fecha/hora de pago (PAGADO)
    daily_number: Optional[int] = None  # Número visible reiniciado a las 22:00 Bogota
    cycle_key: Optional[str] = None  # YYYY-MM-DD del ciclo en America/Bogota
    items: list[OrderItem] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class Notification:
    """Notification domain entity."""
    id: Optional[int] = None
    order_id: int = 0
    event_type: str = ""
    target_role: str = ""
    message: str = ""
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class Category:
    """Category domain entity."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class Subcategory:
    """Subcategory domain entity - additional characteristic for dishes."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class SubcategoryOption:
    """Subcategory option domain entity - available options for a subcategory."""
    id: Optional[int] = None
    subcategory_id: int = 0
    name: str = ""
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


@dataclass
class HistoryLog:
    """History log domain entity."""
    id: Optional[int] = None
    category: str = ""  # ORDENES, PLATOS, LOGIN, USUARIOS
    action: str = ""  # CREADO, ACTUALIZADO, ELIMINADO, LOGIN
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    description: str = ""
    details: Optional[dict] = None
    performed_by: Optional[int] = None
    performed_by_username: Optional[str] = None
    created_at: Optional[datetime] = None
