"""Use cases for notifications."""
from app.infrastructure.database.repositories import NotificationRepository
from app.domain.entities import Notification
from app.shared.exceptions import ValidationException


class GetNotificationUseCase:
    """Use case for getting notification."""
    
    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository
    
    async def execute(self, notification_id: int) -> Notification:
        """Get notification by ID."""
        notification = await self.notification_repository.get_by_id(notification_id)
        if not notification:
            raise ValidationException("Notificación no encontrada")
        return notification


class GetOrderNotificationsUseCase:
    """Use case for getting notifications for an order."""
    
    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository
    
    async def execute(self, order_id: int) -> list[Notification]:
        """Get notifications for order."""
        return await self.notification_repository.get_by_order_id(order_id)


class GetUnreadNotificationsUseCase:
    """Use case for getting unread notifications by role."""
    
    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository
    
    async def execute(self, role: str, skip: int = 0, limit: int = 10) -> list[Notification]:
        """Get unread notifications for role."""
        return await self.notification_repository.get_unread_by_role(role, skip, limit)


class MarkNotificationAsReadUseCase:
    """Use case for marking notification as read."""
    
    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository
    
    async def execute(self, notification_id: int) -> Notification:
        """Mark notification as read."""
        notification = await self.notification_repository.get_by_id(notification_id)
        if not notification:
            raise ValidationException("Notificación no encontrada")
        return await self.notification_repository.mark_as_read(notification_id)
