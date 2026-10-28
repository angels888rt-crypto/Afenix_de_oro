"""Database models using SQLAlchemy 2.0."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, ForeignKey, UniqueConstraint,
    Index, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime, nullable=True, default=None)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)


class UserModel(BaseModel):
    """User model."""
    __tablename__ = "users"
    
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="CAMARERO")
    is_active = Column(Boolean, default=True, nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Relationships
    orders = relationship("OrderModel", back_populates="camarero", foreign_keys="OrderModel.camarero_id")
    
    __table_args__ = (
        Index("idx_username", "username"),
        Index("idx_email", "email"),
        Index("idx_role", "role"),
        CheckConstraint("role IN ('ADMIN', 'CAMARERO', 'CAJERO')", name="ck_user_role"),
    )


class TableModel(BaseModel):
    """Table model."""
    __tablename__ = "tables"
    
    table_number = Column(Integer, nullable=False, unique=True, index=True)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="DISPONIBLE")
    location = Column(String(100), nullable=True)
    
    # Relationships
    orders = relationship("OrderModel", back_populates="table")
    
    __table_args__ = (
        Index("idx_table_number", "table_number"),
        Index("idx_status", "status"),
        CheckConstraint("capacity > 0", name="ck_table_capacity"),
        CheckConstraint("status IN ('DISPONIBLE', 'OCUPADA', 'RESERVADA')", name="ck_table_status"),
    )


class DishModel(BaseModel):
    """Dish/Menu item model."""
    __tablename__ = "dishes"
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)  # Stored in cents to avoid float issues
    estimated_time = Column(Integer, nullable=False)  # In seconds
    category = Column(String(50), nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    preparation_notes = Column(Text, nullable=True)
    image_path = Column(String(255), nullable=True)
    
    # Relationships
    order_items = relationship("OrderItemModel", back_populates="dish")
    
    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_category", "category"),
        CheckConstraint("price > 0", name="ck_dish_price"),
        CheckConstraint("estimated_time > 0", name="ck_dish_time"),
    )


class OrderModel(BaseModel):
    """Order model."""
    __tablename__ = "orders"
    
    table_id = Column(Integer, ForeignKey("tables.id", ondelete="RESTRICT"), nullable=False, index=True)
    camarero_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="PENDIENTE", index=True)
    total_amount = Column(Integer, default=0, nullable=False)  # In cents
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    # Número visible reiniciado diariamente a las 22:00 America/Bogota
    daily_number = Column(Integer, nullable=True, index=True)
    cycle_key = Column(String(20), nullable=True, index=True)  # YYYY-MM-DD de inicio de ciclo en Bogota
    
    # Relationships
    table = relationship("TableModel", back_populates="orders")
    camarero = relationship("UserModel", back_populates="orders", foreign_keys=[camarero_id])
    items = relationship("OrderItemModel", back_populates="order", cascade="all, delete-orphan")
    notifications = relationship("NotificationModel", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_table_id", "table_id"),
        Index("idx_camarero_id", "camarero_id"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
        Index("idx_daily_number", "daily_number"),
        Index("idx_cycle_key", "cycle_key"),
        UniqueConstraint("cycle_key", "daily_number", name="uq_cycle_daily_number"),
        CheckConstraint("status IN ('PENDIENTE', 'NUEVO', 'EN_COCINA', 'COMPLETADO', 'ENTREGADO', 'CANCELADO', 'PAGADO')", name="ck_order_status"),
    )


class OrderItemModel(BaseModel):
    """Order item model."""
    __tablename__ = "order_items"
    
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Integer, nullable=False)  # In cents, price at time of order
    status = Column(String(20), nullable=False, default="PENDIENTE", index=True)
    special_notes = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("OrderModel", back_populates="items")
    dish = relationship("DishModel", back_populates="order_items")
    
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_dish_id", "dish_id"),
        Index("idx_status", "status"),
        CheckConstraint("quantity > 0", name="ck_orderitem_quantity"),
        CheckConstraint("status IN ('PENDIENTE', 'EN_PREPARACION', 'LISTO', 'ENTREGADO', 'CANCELADO')", name="ck_orderitem_status"),
    )


class NotificationModel(BaseModel):
    """Notification model."""
    __tablename__ = "notifications"
    
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    target_role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("OrderModel", back_populates="notifications")
    
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_event_type", "event_type"),
        Index("idx_target_role", "target_role"),
        Index("idx_is_read", "is_read"),
    )


class HistoryLogModel(Base):
    """History / audit log model — stores all activity for admin-historial.

    Retention: ~4 days, cleaned daily at 06:00 America/Bogota.
    Categories:
      ORDENES — creación, actualización y eliminación de órdenes
      PLATOS  — platos creados, actualizados y eliminados
      LOGIN   — registros de inicios de sesión (usuarios ingresados)
      USUARIOS — usuarios creados, actualizados y eliminados
    """
    __tablename__ = "history_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    category = Column(String(30), nullable=False, index=True)
    action = Column(String(30), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    entity_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    performed_by = Column(Integer, nullable=True)
    performed_by_username = Column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_history_category", "category"),
        Index("idx_history_action", "action"),
        Index("idx_history_created_at", "created_at"),
        Index("idx_history_entity", "entity_type", "entity_id"),
        CheckConstraint(
            "category IN ('ORDENES','PLATOS','LOGIN','USUARIOS')",
            name="ck_history_category",
        ),
        CheckConstraint(
            "action IN ('CREADO','ACTUALIZADO','ELIMINADO','LOGIN')",
            name="ck_history_action",
        ),
    )


class ReceiptConfigModel(Base):
    """Configuración del recibo térmico — singleton (id=1).
    Almacena logo, nombre del restaurante y mensaje final.
    """
    __tablename__ = "receipt_config"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_name = Column(String(100), nullable=False, default="RESTAURANTE")
    footer_message = Column(Text, nullable=False, default="¡Gracias por su visita!")
    logo_path = Column(String(255), nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CategoryModel(BaseModel):
    """Category model."""
    __tablename__ = "categories"

    name = Column(String(80), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_category_name", "name"),
    )


class SubcategoryModel(BaseModel):
    """Subcategory model - additional characteristic for dishes."""
    __tablename__ = "subcategories"

    name = Column(String(80), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_subcategory_name", "name"),
    )


class SubcategoryOptionModel(BaseModel):
    """Subcategory option model - available options for a subcategory."""
    __tablename__ = "subcategory_options"

    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(80), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_option_subcategory", "subcategory_id"),
    )


class DishSubcategoryModel(BaseModel):
    """Link between dishes and subcategories - many to many."""
    __tablename__ = "dish_subcategories"

    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        Index("idx_dish_subcategory_dish", "dish_id"),
        Index("idx_dish_subcategory_subcategory", "subcategory_id"),
    )


class OrderItemSubcategorySelectionModel(BaseModel):
    """Selection made by waiter for a subcategory option within an order item."""
    __tablename__ = "order_item_subcategory_selections"

    order_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="CASCADE"), nullable=False, index=True)
    option_id = Column(Integer, ForeignKey("subcategory_options.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        Index("idx_selection_order_item", "order_item_id"),
        Index("idx_selection_subcategory", "subcategory_id"),
        Index("idx_selection_option", "option_id"),
    )


