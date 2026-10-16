from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "ADMIN"
    CAMARERO = "CAMARERO"
    CAJERO = "CAJERO"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDIENTE = "PENDIENTE"
    NUEVO = "NUEVO"
    EN_COCINA = "EN_COCINA"
    COMPLETADO = "COMPLETADO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"
    PAGADO = "PAGADO"


class OrderItemStatus(str, Enum):
    """Order item status enumeration."""
    PENDIENTE = "PENDIENTE"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO = "LISTO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class TableStatus(str, Enum):
    """Table status enumeration."""
    DISPONIBLE = "DISPONIBLE"
    OCUPADA = "OCUPADA"
    RESERVADA = "RESERVADA"


class NotificationEvent(str, Enum):
    """Notification event types."""
    NUEVO_PEDIDO = "NUEVO_PEDIDO"
    PLATO_LISTO = "PLATO_LISTO"
    PEDIDO_COMPLETADO = "PEDIDO_COMPLETADO"
    PEDIDO_ENTREGADO = "PEDIDO_ENTREGADO"
    PEDIDO_CANCELADO = "PEDIDO_CANCELADO"
