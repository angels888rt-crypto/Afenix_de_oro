"""Order and notification repositories."""
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.models import (
    OrderModel, OrderItemModel, NotificationModel, DishModel
)
from app.domain.entities import (
    Order, OrderItem, Notification
)


class OrderRepository:
    """Order repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, order: Order) -> Order:
        """Create a new order."""
        db_order = OrderModel(
            table_id=order.table_id,
            camarero_id=order.camarero_id,
            status=order.status.value if hasattr(order.status, 'value') else order.status,
            total_amount=order.total_amount,
            notes=order.notes,
            daily_number=order.daily_number,
            cycle_key=order.cycle_key,
            created_by=order.created_by,
        )
        self.session.add(db_order)
        await self.session.commit()
        await self.session.refresh(db_order)
        
        # Add items
        for item in order.items:
            db_item = OrderItemModel(
                order_id=db_order.id,
                dish_id=item.dish_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                status=item.status.value if hasattr(item.status, 'value') else item.status,
                special_notes=item.special_notes,
                created_by=order.created_by,
            )
            self.session.add(db_item)
        
        await self.session.commit()
        await self.session.refresh(db_order)
        return await self._to_domain_with_items(db_order)
    
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        result = await self.session.execute(
            select(OrderModel).where(
                OrderModel.id == order_id,
                OrderModel.deleted_at.is_(None)
            )
        )
        order = result.scalars().first()
        return await self._to_domain_with_items(order) if order else None
    
    async def get_by_table_id(self, table_id: int) -> Optional[Order]:
        """Get active order for table."""
        result = await self.session.execute(
            select(OrderModel).where(
                OrderModel.table_id == table_id,
                OrderModel.status.in_(["PENDIENTE", "NUEVO", "EN_COCINA", "COMPLETADO"]),
                OrderModel.deleted_at.is_(None)
            ).order_by(OrderModel.created_at.desc())
        )
        order = result.scalars().first()
        return await self._to_domain_with_items(order) if order else None
    
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 10) -> list[Order]:
        """Get orders by status."""
        result = await self.session.execute(
            select(OrderModel).where(
                OrderModel.status == status,
                OrderModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return [await self._to_domain_with_items(order) for order in orders]
    
    async def get_by_camarero_id(self, camarero_id: int, skip: int = 0, limit: int = 10) -> list[Order]:
        """Get orders by camarero - solo ciclo actual 22:00 Bogota (filtra antiguas)."""
        from datetime import timedelta
        try:
            from zoneinfo import ZoneInfo
            BOGOTA_TZ = ZoneInfo("America/Bogota")
        except Exception:
            BOGOTA_TZ = timezone(timedelta(hours=-5))
        def _cycle_key_now():
            now_utc = datetime.now(timezone.utc)
            now_bog = now_utc.astimezone(BOGOTA_TZ)
            cd = now_bog.date()
            cs = datetime.combine(cd, datetime.min.time()).replace(tzinfo=BOGOTA_TZ) + timedelta(hours=22)
            if now_bog < cs:
                cs -= timedelta(days=1)
                cd = cs.date()
            return cd.isoformat()
        cycle_key = _cycle_key_now()
        result = await self.session.execute(
            select(OrderModel).where(
                OrderModel.camarero_id == camarero_id,
                OrderModel.cycle_key == cycle_key,
                OrderModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return [await self._to_domain_with_items(order) for order in orders]

    async def get_pending_for_cajero(self, cycle_key: str, skip: int = 0, limit: int = 100) -> list[Order]:
        """Get pending orders for CAJERO - only current cycle."""
        result = await self.session.execute(
            select(OrderModel).where(
                OrderModel.status.in_(["PENDIENTE", "NUEVO"]),
                OrderModel.cycle_key == cycle_key,
                OrderModel.deleted_at.is_(None)
            ).order_by(OrderModel.created_at.asc()).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return [await self._to_domain_with_items(order) for order in orders]

    async def get_entregados_for_cajero(self, cycle_key: str = None, skip: int = 0, limit: int = 100) -> list[Order]:
        """Get ENTREGADO orders for CAJERO - filtered by cycle if provided."""
        from sqlalchemy import and_
        conditions = [
            OrderModel.status == "ENTREGADO",
            OrderModel.deleted_at.is_(None)
        ]
        if cycle_key is not None:
            conditions.append(OrderModel.cycle_key == cycle_key)
        result = await self.session.execute(
            select(OrderModel).where(*conditions).order_by(OrderModel.created_at.asc()).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return [await self._to_domain_with_items(order) for order in orders]

    async def get_pagado_orders_filtered(self, start_date=None, end_date=None, dish_id=None, camarero_id=None, skip: int = 0, limit: int = 100) -> list[Order]:
        """Get PAGADO orders filtered by date range, dish, and waiter - for sales report."""
        from sqlalchemy import and_, select
        conditions = [
            OrderModel.status == "PAGADO",
            OrderModel.deleted_at.is_(None)
        ]
        if start_date is not None:
            conditions.append(OrderModel.created_at >= start_date)
        if end_date is not None:
            conditions.append(OrderModel.created_at <= end_date)
        if camarero_id is not None:
            conditions.append(OrderModel.camarero_id == camarero_id)
        if dish_id is not None:
            subq = select(OrderItemModel.order_id).where(
                OrderItemModel.dish_id == dish_id,
                OrderItemModel.deleted_at.is_(None)
            )
            conditions.append(OrderModel.id.in_(subq))
        result = await self.session.execute(
            select(OrderModel).where(*conditions).order_by(OrderModel.created_at.desc()).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return [await self._to_domain_with_items(order) for order in orders]

    async def get_sales_aggregation(self, start_date=None, end_date=None, dish_id=None, camarero_id=None) -> dict:
        """Return aggregated sales data for PAGADO orders with given filters."""
        orders = await self.get_pagado_orders_filtered(start_date, end_date, dish_id, camarero_id, skip=0, limit=10000)
        total_sales = 0
        total_dishes_sold = 0
        num_orders = len(orders)
        per_dish = {}
        for o in orders:
            total_sales += o.total_amount or 0
            for it in o.items:
                if dish_id is not None and it.dish_id != dish_id:
                    continue
                qty = it.quantity or 0
                total_dishes_sold += qty
                key = it.dish_id
                if key not in per_dish:
                    per_dish[key] = {"dish_id": it.dish_id, "dish_name": it.dish_name or f"Plato #{it.dish_id}", "quantity": 0, "total_cents": 0}
                per_dish[key]["quantity"] += qty
                per_dish[key]["total_cents"] += (it.unit_price or 0) * qty
        platos_vendidos = sorted(per_dish.values(), key=lambda x: x["quantity"], reverse=True)
        return {
            "num_orders_pagadas": num_orders,
            "total_platos_vendidos": total_dishes_sold,
            "total_ventas_cents": total_sales,
            "total_ventas_formatted": f"${total_sales/100:.2f}",
            "platos": platos_vendidos,
            "orders": orders
        }

    async def update_with_items(self, order_id: int, new_items: list[dict], total_amount: int, notes: Optional[str], updated_by: Optional[int]) -> Optional[Order]:
        """Replace order items and update totals - for mesero editing pending orders."""
        # Load order
        result = await self.session.execute(select(OrderModel).where(OrderModel.id == order_id, OrderModel.deleted_at.is_(None)))
        db_order = result.scalars().first()
        if not db_order:
            return None
        # Delete existing items (soft? we hard delete for simplicity and recreate)
        # First, mark existing items as deleted
        existing = await self.session.execute(select(OrderItemModel).where(OrderItemModel.order_id == order_id, OrderItemModel.deleted_at.is_(None)))
        for item in existing.scalars().all():
            item.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        # Create new items
        for it in new_items:
            db_item = OrderItemModel(
                order_id=order_id,
                dish_id=it["dish_id"],
                quantity=it["quantity"],
                unit_price=it["unit_price"],
                status=it.get("status", "PENDIENTE"),
                special_notes=it.get("special_notes"),
                created_by=updated_by,
            )
            self.session.add(db_item)
        db_order.total_amount = total_amount
        if notes is not None:
            db_order.notes = notes
        db_order.updated_at = datetime.now(timezone.utc)
        db_order.updated_by = updated_by
        await self.session.commit()
        await self.session.refresh(db_order)
        return await self._to_domain_with_items(db_order)
    
    async def update(self, order_id: int, order: Order) -> Optional[Order]:
        """Update order."""
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        result = await self.session.execute(stmt)
        db_order = result.scalars().first()
        
        if not db_order:
            return None
        
        if order.status:
            db_order.status = order.status.value if hasattr(order.status, 'value') else order.status
        if order.notes is not None:
            db_order.notes = order.notes
        if order.total_amount:
            db_order.total_amount = order.total_amount
        if order.started_at is not None:
            db_order.started_at = order.started_at
        if order.completed_at is not None:
            db_order.completed_at = order.completed_at
        if order.delivered_at is not None:
            db_order.delivered_at = order.delivered_at
        if getattr(order, 'paid_at', None) is not None:
            db_order.paid_at = order.paid_at
        
        db_order.updated_at = datetime.now(timezone.utc)
        db_order.updated_by = order.updated_by
        
        await self.session.commit()
        return await self._to_domain_with_items(db_order)
    
    async def delete(self, order_id: int) -> bool:
        """Soft delete order."""
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        result = await self.session.execute(stmt)
        db_order = result.scalars().first()
        
        if not db_order:
            return False
        
        db_order.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True
    
    async def get_max_daily_number(self, cycle_key: str) -> Optional[int]:
        """Obtiene el máximo daily_number para un ciclo dado."""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.max(OrderModel.daily_number)).where(
                OrderModel.cycle_key == cycle_key,
                OrderModel.deleted_at.is_(None)
            )
        )
        max_val = result.scalar()
        return int(max_val) if max_val is not None else None

    async def list_by_cycle(self, cycle_key: str) -> list[Order]:
        """Lista órdenes de un ciclo específico."""
        result = await self.session.execute(
            select(OrderModel).where(
                OrderModel.cycle_key == cycle_key,
                OrderModel.deleted_at.is_(None)
            )
        )
        orders = result.scalars().all()
        return [await self._to_domain_with_items(o) for o in orders]

    async def delete_all(self) -> int:
        """Elimina (soft delete) todos los pedidos visibles en mesero-pedidos. Se ejecuta a las 22:00 Bogota."""
        from sqlalchemy import update
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            update(OrderModel).where(
                OrderModel.deleted_at.is_(None),
                OrderModel.status.notin_(["PAGADO", "CANCELADO"])
            ).values(deleted_at=now, updated_at=now)
        )
        await self.session.commit()
        return result.rowcount or 0

    async def list(self, skip: int = 0, limit: int = 10) -> list[Order]:
        """List orders."""
        result = await self.session.execute(
            select(OrderModel).where(
                OrderModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return [await self._to_domain_with_items(order) for order in orders]
    
    async def _to_domain_with_items(self, db_order: OrderModel) -> Order:
        """Convert database model to domain entity with items."""
        # Load items
        items_result = await self.session.execute(
            select(OrderItemModel, DishModel.name)
            .join(DishModel, DishModel.id == OrderItemModel.dish_id)
            .where(
                OrderItemModel.order_id == db_order.id,
                OrderItemModel.deleted_at.is_(None)
            )
        )
        item_rows = items_result.all()
        
        order_items = [
            OrderItem(
                id=item.id,
                order_id=item.order_id,
                dish_id=item.dish_id,
                dish_name=dish_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                status=item.status,
                special_notes=item.special_notes,
                started_at=item.started_at,
                completed_at=item.completed_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
                deleted_at=item.deleted_at,
                created_by=item.created_by,
                updated_by=item.updated_by,
            )
            for item, dish_name in item_rows
        ]

        # Fetch table_number for display (correct Mesa)
        table_number = None
        try:
            from app.infrastructure.database.models import TableModel
            t_res = await self.session.execute(
                select(TableModel.table_number).where(TableModel.id == db_order.table_id)
            )
            row = t_res.scalars().first()
            if row is not None:
                table_number = int(row)
        except Exception:
            table_number = None
        
        return Order(
            id=db_order.id,
            table_id=db_order.table_id,
            table_number=table_number,
            camarero_id=db_order.camarero_id,
            status=db_order.status,
            total_amount=db_order.total_amount,
            notes=db_order.notes,
            daily_number=db_order.daily_number,
            cycle_key=db_order.cycle_key,
            items=order_items,
            started_at=db_order.started_at,
            completed_at=db_order.completed_at,
            delivered_at=db_order.delivered_at,
            paid_at=getattr(db_order, 'paid_at', None),
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
            deleted_at=db_order.deleted_at,
            created_by=db_order.created_by,
            updated_by=db_order.updated_by,
        )


class OrderItemRepository:
    """Order item repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, order_item: OrderItem) -> OrderItem:
        """Create a new order item."""
        db_item = OrderItemModel(
            order_id=order_item.order_id,
            dish_id=order_item.dish_id,
            quantity=order_item.quantity,
            unit_price=order_item.unit_price,
            status=order_item.status.value if hasattr(order_item.status, 'value') else order_item.status,
            special_notes=order_item.special_notes,
            created_by=order_item.created_by,
        )
        self.session.add(db_item)
        await self.session.commit()
        await self.session.refresh(db_item)
        return self._to_domain(db_item)
    
    async def get_by_id(self, item_id: int) -> Optional[OrderItem]:
        """Get order item by ID."""
        result = await self.session.execute(
            select(OrderItemModel).where(
                OrderItemModel.id == item_id,
                OrderItemModel.deleted_at.is_(None)
            )
        )
        item = result.scalars().first()
        return self._to_domain(item) if item else None
    
    async def get_by_order_id(self, order_id: int) -> list[OrderItem]:
        """Get items for order."""
        result = await self.session.execute(
            select(OrderItemModel).where(
                OrderItemModel.order_id == order_id,
                OrderItemModel.deleted_at.is_(None)
            )
        )
        items = result.scalars().all()
        return [self._to_domain(item) for item in items]
    
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 10) -> list[OrderItem]:
        """Get order items by status."""
        result = await self.session.execute(
            select(OrderItemModel).where(
                OrderItemModel.status == status,
                OrderItemModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        items = result.scalars().all()
        return [self._to_domain(item) for item in items]
    
    async def update(self, item_id: int, order_item: OrderItem) -> Optional[OrderItem]:
        """Update order item."""
        stmt = select(OrderItemModel).where(OrderItemModel.id == item_id)
        result = await self.session.execute(stmt)
        db_item = result.scalars().first()
        
        if not db_item:
            return None
        
        if order_item.quantity:
            db_item.quantity = order_item.quantity
        if order_item.status:
            db_item.status = order_item.status.value if hasattr(order_item.status, 'value') else order_item.status
        if order_item.special_notes is not None:
            db_item.special_notes = order_item.special_notes
        if order_item.started_at is not None:
            db_item.started_at = order_item.started_at
        if order_item.completed_at is not None:
            db_item.completed_at = order_item.completed_at
        
        db_item.updated_at = datetime.now(timezone.utc)
        db_item.updated_by = order_item.updated_by
        
        await self.session.commit()
        return self._to_domain(db_item)
    
    async def delete(self, item_id: int) -> bool:
        """Soft delete order item."""
        stmt = select(OrderItemModel).where(OrderItemModel.id == item_id)
        result = await self.session.execute(stmt)
        db_item = result.scalars().first()
        
        if not db_item:
            return False
        
        db_item.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True
    
    async def list(self, skip: int = 0, limit: int = 10) -> list[OrderItem]:
        """List order items."""
        result = await self.session.execute(
            select(OrderItemModel).where(
                OrderItemModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        items = result.scalars().all()
        return [self._to_domain(item) for item in items]
    
    @staticmethod
    def _to_domain(db_item: OrderItemModel) -> OrderItem:
        """Convert database model to domain entity."""
        return OrderItem(
            id=db_item.id,
            order_id=db_item.order_id,
            dish_id=db_item.dish_id,
            quantity=db_item.quantity,
            unit_price=db_item.unit_price,
            status=db_item.status,
            special_notes=db_item.special_notes,
            started_at=db_item.started_at,
            completed_at=db_item.completed_at,
            created_at=db_item.created_at,
            updated_at=db_item.updated_at,
            deleted_at=db_item.deleted_at,
            created_by=db_item.created_by,
            updated_by=db_item.updated_by,
        )


class NotificationRepository:
    """Notification repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, notification: Notification) -> Notification:
        """Create a new notification."""
        db_notification = NotificationModel(
            order_id=notification.order_id,
            event_type=notification.event_type,
            target_role=notification.target_role,
            message=notification.message,
            is_read=notification.is_read,
            created_by=notification.created_by,
        )
        self.session.add(db_notification)
        await self.session.commit()
        await self.session.refresh(db_notification)
        return self._to_domain(db_notification)
    
    async def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID."""
        result = await self.session.execute(
            select(NotificationModel).where(
                NotificationModel.id == notification_id,
                NotificationModel.deleted_at.is_(None)
            )
        )
        notification = result.scalars().first()
        return self._to_domain(notification) if notification else None
    
    async def get_by_order_id(self, order_id: int) -> list[Notification]:
        """Get notifications for order."""
        result = await self.session.execute(
            select(NotificationModel).where(
                NotificationModel.order_id == order_id,
                NotificationModel.deleted_at.is_(None)
            )
        )
        notifications = result.scalars().all()
        return [self._to_domain(notif) for notif in notifications]
    
    async def get_unread_by_role(self, role: str, skip: int = 0, limit: int = 10) -> list[Notification]:
        """Get unread notifications for role."""
        result = await self.session.execute(
            select(NotificationModel).where(
                NotificationModel.target_role == role,
                NotificationModel.is_read == False,
                NotificationModel.deleted_at.is_(None)
            ).offset(skip).limit(limit).order_by(NotificationModel.created_at.desc())
        )
        notifications = result.scalars().all()
        return [self._to_domain(notif) for notif in notifications]
    
    async def mark_as_read(self, notification_id: int) -> Optional[Notification]:
        """Mark notification as read."""
        stmt = select(NotificationModel).where(NotificationModel.id == notification_id)
        result = await self.session.execute(stmt)
        db_notif = result.scalars().first()
        
        if not db_notif:
            return None
        
        db_notif.is_read = True
        db_notif.read_at = datetime.now(timezone.utc)
        db_notif.updated_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(db_notif)
        return self._to_domain(db_notif)
    
    async def update(self, notification_id: int, notification: Notification) -> Optional[Notification]:
        """Update notification."""
        return await self.mark_as_read(notification_id)
    
    async def delete(self, notification_id: int) -> bool:
        """Soft delete notification."""
        stmt = select(NotificationModel).where(NotificationModel.id == notification_id)
        result = await self.session.execute(stmt)
        db_notif = result.scalars().first()
        
        if not db_notif:
            return False
        
        db_notif.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(db_notif)
        return True
    
    async def list(self, skip: int = 0, limit: int = 10) -> list[Notification]:
        """List notifications."""
        result = await self.session.execute(
            select(NotificationModel).where(
                NotificationModel.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        notifications = result.scalars().all()
        return [self._to_domain(notif) for notif in notifications]
    
    @staticmethod
    def _to_domain(db_notif: NotificationModel) -> Notification:
        """Convert database model to domain entity."""
        return Notification(
            id=db_notif.id,
            order_id=db_notif.order_id,
            event_type=db_notif.event_type,
            target_role=db_notif.target_role,
            message=db_notif.message,
            is_read=db_notif.is_read,
            read_at=db_notif.read_at,
            created_at=db_notif.created_at,
            updated_at=db_notif.updated_at,
            deleted_at=db_notif.deleted_at,
            created_by=db_notif.created_by,
            updated_by=db_notif.updated_by,
        )
