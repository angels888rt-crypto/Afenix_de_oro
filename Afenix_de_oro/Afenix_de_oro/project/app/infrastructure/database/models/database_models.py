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
        CheckConstraint("role IN ('ADMIN', 'CAMARERO', 'CAJERO', 'MONITOR')", name="ck_user_role"),
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


class CategoryModel(BaseModel):
    """Category model for dish grouping."""
    __tablename__ = "categories"

    name = Column(String(80), nullable=False, unique=True, index=True)
    description = Column(String(200), nullable=True)

    # Relationships
    dishes = relationship("DishModel", back_populates="category_obj")

    __table_args__ = (
        Index("idx_category_name", "name"),
        UniqueConstraint("name", name="uq_category_name"),
    )


class DishSubcategoryAssociation(Base):
    """Association table dish <-> subcategory (many-to-many)."""
    __tablename__ = "dish_subcategories"

    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        Index("idx_dish_sub", "dish_id", "subcategory_id"),
        Index("idx_sub_dish", "subcategory_id", "dish_id"),
    )


class SubcategoryModel(BaseModel):
    """Subcategory model - mandatory options for specific dishes."""
    __tablename__ = "subcategories"

    name = Column(String(80), nullable=False, unique=True, index=True)
    description = Column(String(200), nullable=True)

    # Relationships
    options = relationship("SubcategoryOptionModel", back_populates="subcategory", cascade="all, delete-orphan")
    dishes = relationship("DishModel", secondary="dish_subcategories", back_populates="subcategories")

    __table_args__ = (
        Index("idx_subcategory_name", "name"),
        UniqueConstraint("name", name="uq_subcategory_name"),
    )


class SubcategoryOptionModel(BaseModel):
    """Option for a subcategory."""
    __tablename__ = "subcategory_options"

    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(80), nullable=False, index=True)

    subcategory = relationship("SubcategoryModel", back_populates="options")

    __table_args__ = (
        Index("idx_option_sub_name", "subcategory_id", "name"),
        UniqueConstraint("subcategory_id", "name", name="uq_option_per_subcategory"),
    )


class DishModel(BaseModel):
    """Dish/Menu item model."""
    __tablename__ = "dishes"
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)  # Stored in cents to avoid float issues
    estimated_time = Column(Integer, nullable=False)  # In seconds
    category = Column(String(50), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    preparation_notes = Column(Text, nullable=True)
    image_path = Column(String(255), nullable=True)
    
    # Relationships
    order_items = relationship("OrderItemModel", back_populates="dish")
    category_obj = relationship("CategoryModel", back_populates="dishes")
    subcategories = relationship("SubcategoryModel", secondary="dish_subcategories", back_populates="dishes")
    
    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_category", "category"),
        Index("idx_category_id", "category_id"),
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
    subcategory_selections = relationship("OrderItemSubcategorySelectionModel", back_populates="order_item", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_dish_id", "dish_id"),
        Index("idx_status", "status"),
        CheckConstraint("quantity > 0", name="ck_orderitem_quantity"),
        CheckConstraint("status IN ('PENDIENTE', 'EN_PREPARACION', 'LISTO', 'ENTREGADO', 'CANCELADO')", name="ck_orderitem_status"),
    )


class OrderItemSubcategorySelectionModel(Base):
    """Selection of subcategory option per order item (mandatory)."""
    __tablename__ = "order_item_subcategory_selections"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id", ondelete="RESTRICT"), nullable=False, index=True)
    option_id = Column(Integer, ForeignKey("subcategory_options.id", ondelete="RESTRICT"), nullable=False, index=True)
    subcategory_name = Column(String(80), nullable=False)
    option_name = Column(String(80), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    order_item = relationship("OrderItemModel", back_populates="subcategory_selections")
    subcategory = relationship("SubcategoryModel")
    option = relationship("SubcategoryOptionModel")

    __table_args__ = (
        Index("idx_oi_sub", "order_item_id", "subcategory_id"),
        UniqueConstraint("order_item_id", "subcategory_id", name="uq_oi_subcategory"),
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
