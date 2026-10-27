"""Notification API routers."""
from fastapi import APIRouter, Depends, status, Query

from app.infrastructure.database.repositories import NotificationRepository
from app.application.use_cases.notification_use_cases import (
    GetNotificationUseCase, GetOrderNotificationsUseCase, GetUnreadNotificationsUseCase,
    MarkNotificationAsReadUseCase
)
from app.application.dto import NotificationResponse
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_notification_repository, get_current_user
)

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/{notification_id}", response_model=ResponseSchema[NotificationResponse])
async def get_notification(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
):
    """Get notification by ID."""
    use_case = GetNotificationUseCase(notification_repository)
    notification = await use_case.execute(notification_id)
    
    return ResponseSchema(
        success=True,
        message="Notificación obtenida exitosamente",
        data=NotificationResponse(
            id=notification.id,
            order_id=notification.order_id,
            event_type=notification.event_type,
            target_role=notification.target_role,
            message=notification.message,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
        )
    )


@router.get("/order/{order_id}", response_model=ResponseSchema[list[NotificationResponse]])
async def get_order_notifications(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
):
    """Get notifications for an order."""
    use_case = GetOrderNotificationsUseCase(notification_repository)
    notifications = await use_case.execute(order_id)
    
    return ResponseSchema(
        success=True,
        message="Notificaciones obtenidas exitosamente",
        data=[
            NotificationResponse(
                id=notif.id,
                order_id=notif.order_id,
                event_type=notif.event_type,
                target_role=notif.target_role,
                message=notif.message,
                is_read=notif.is_read,
                read_at=notif.read_at,
                created_at=notif.created_at,
            )
            for notif in notifications
        ]
    )


@router.get("/unread", response_model=ResponseSchema[list[NotificationResponse]])
async def get_unread_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
):
    """Get unread notifications for current user's role."""
    use_case = GetUnreadNotificationsUseCase(notification_repository)
    notifications = await use_case.execute(current_user["role"], skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Notificaciones sin leer obtenidas exitosamente",
        data=[
            NotificationResponse(
                id=notif.id,
                order_id=notif.order_id,
                event_type=notif.event_type,
                target_role=notif.target_role,
                message=notif.message,
                is_read=notif.is_read,
                read_at=notif.read_at,
                created_at=notif.created_at,
            )
            for notif in notifications
        ]
    )


@router.put("/{notification_id}/read", response_model=ResponseSchema[NotificationResponse])
async def mark_as_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
):
    """Mark notification as read."""
    use_case = MarkNotificationAsReadUseCase(notification_repository)
    notification = await use_case.execute(notification_id)
    
    return ResponseSchema(
        success=True,
        message="Notificación marcada como leída",
        data=NotificationResponse(
            id=notification.id,
            order_id=notification.order_id,
            event_type=notification.event_type,
            target_role=notification.target_role,
            message=notification.message,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
        )
    )
