"""Domain services."""
from datetime import datetime, timezone


class OrderService:
    """Service for business logic related to orders."""
    
    @staticmethod
    def calculate_total_amount(items: list[dict]) -> int:
        """Calculate total amount from order items."""
        return sum(item.get("unit_price", 0) * item.get("quantity", 0) for item in items)
    
    @staticmethod
    def start_order(order) -> None:
        """Mark order as started (in kitchen)."""
        if order.started_at is None:
            order.started_at = datetime.now(timezone.utc)
    
    @staticmethod
    def complete_order(order) -> None:
        """Mark order as completed."""
        if order.completed_at is None:
            order.completed_at = datetime.now(timezone.utc)
    
    @staticmethod
    def deliver_order(order) -> None:
        """Mark order as delivered."""
        if order.delivered_at is None:
            order.delivered_at = datetime.now(timezone.utc)

    @staticmethod
    def pay_order(order) -> None:
        """Mark order as paid (PAGADO)."""
        if getattr(order, 'paid_at', None) is None:
            order.paid_at = datetime.now(timezone.utc)
        if order.completed_at is None:
            order.completed_at = datetime.now(timezone.utc)


class OrderItemService:
    """Service for business logic related to order items."""
    
    @staticmethod
    def start_item(item) -> None:
        """Mark item as started (being prepared)."""
        if item.started_at is None:
            item.started_at = datetime.now(timezone.utc)
    
    @staticmethod
    def complete_item(item) -> None:
        """Mark item as completed (ready to serve)."""
        if item.completed_at is None:
            item.completed_at = datetime.now(timezone.utc)
    
    @staticmethod
    def get_preparation_time(item) -> int:
        """Get actual preparation time in seconds."""
        if item.started_at and item.completed_at:
            return int((item.completed_at - item.started_at).total_seconds())
        return 0


class NotificationService:
    """Service for business logic related to notifications."""
    
    @staticmethod
    def should_notify_camarero(event_type: str) -> bool:
        """Determine if camareros should be notified."""
        return event_type in ["PLATO_LISTO", "PEDIDO_COMPLETADO", "PLATO_CANCELADO"]
