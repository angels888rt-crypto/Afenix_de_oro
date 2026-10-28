"""Use cases for order management."""
from typing import Optional
from datetime import datetime, timezone, timedelta

from app.infrastructure.database.repositories import (
    OrderRepository, OrderItemRepository, DishRepository, NotificationRepository, TableRepository
)
from app.domain.entities import Order, OrderItem, Notification
from app.domain.services import OrderService, OrderItemService, NotificationService
from app.shared.exceptions import ValidationException, ConflictException
from app.shared.constants.enums import OrderStatus, OrderItemStatus, NotificationEvent

try:
    from zoneinfo import ZoneInfo
    BOGOTA_TZ = ZoneInfo("America/Bogota")
except Exception:
    BOGOTA_TZ = timezone(timedelta(hours=-5))

def _get_bogota_now() -> datetime:
    return datetime.now(BOGOTA_TZ)

def _get_cycle_for_timestamp(dt_utc: Optional[datetime] = None) -> tuple[str, datetime]:
    """Devuelve (cycle_key, cycle_start_utc) para un timestamp UTC dado.
    Ciclo = [22:00 Bogota, 22:00 Bogota siguiente). cycle_key = YYYY-MM-DD de inicio en Bogota."""
    if dt_utc is None:
        dt_utc = datetime.now(timezone.utc)
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    dt_bogota = dt_utc.astimezone(BOGOTA_TZ)
    # Determina el inicio del ciclo: último 22:00 en Bogota
    cycle_date_bogota = dt_bogota.date()
    cycle_start_bogota = datetime.combine(cycle_date_bogota, datetime.min.time()).replace(tzinfo=BOGOTA_TZ) + timedelta(hours=22)
    if dt_bogota < cycle_start_bogota:
        # Antes de las 22:00, el ciclo es el de ayer
        cycle_start_bogota -= timedelta(days=1)
        cycle_date_bogota = cycle_start_bogota.date()
    cycle_key = cycle_date_bogota.isoformat()  # YYYY-MM-DD
    cycle_start_utc = cycle_start_bogota.astimezone(timezone.utc)
    return cycle_key, cycle_start_utc


class CreateOrderUseCase:
    """Use case for creating an order."""
    
    def __init__(self, order_repository: OrderRepository, dish_repository: DishRepository, table_repository: TableRepository, notification_repository: NotificationRepository):
        self.order_repository = order_repository
        self.dish_repository = dish_repository
        self.table_repository = table_repository
        self.notification_repository = notification_repository
    
    async def execute(self, table_id: Optional[int] = None, table_number: Optional[int] = None, items_data: Optional[list[dict]] = None, notes: Optional[str] = None, camarero_id: Optional[int] = None, created_by: Optional[int] = None) -> Order:
        """Create an order from an existing table or an arbitrary table number."""
        table = None
        if table_id is not None:
            table = await self.table_repository.get_by_id(table_id)
        elif table_number is not None:
            # Step 1: look for an active (non-deleted) table first
            table = await self.table_repository.get_by_number(table_number)

            if not table:
                # Step 2: check whether the table exists but was soft-deleted.
                # get_by_number with include_deleted=True sees all rows including
                # rows where deleted_at IS NOT NULL.
                deleted_table = await self.table_repository.get_by_number(
                    table_number, include_deleted=True
                )

                if deleted_table:
                    # Restore the soft-deleted row instead of creating a duplicate,
                    # which would violate the UNIQUE constraint on table_number.
                    from app.domain.entities import Table
                    from app.shared.constants.enums import TableStatus
                    deleted_table.status = TableStatus.DISPONIBLE.value
                    deleted_table.location = deleted_table.location or "Creada desde pedido"
                    deleted_table.updated_by = created_by
                    deleted_table.deleted_at = None
                    table = await self.table_repository.restore(deleted_table)
                else:
                    # Step 3: table genuinely does not exist — create it.
                    # The try/except guards against a race condition where two
                    # concurrent requests for the same non-existent table_number
                    # both pass the get_by_number check and both attempt create.
                    # The loser gets an IntegrityError and falls back to reading
                    # the row the winner just inserted.
                    from app.domain.entities import Table
                    from app.shared.constants.enums import TableStatus
                    try:
                        table = await self.table_repository.create(Table(
                            table_number=table_number,
                            capacity=4,
                            status=TableStatus.DISPONIBLE.value,
                            location="Creada desde pedido",
                            created_by=created_by,
                            updated_by=created_by,
                        ))
                    except Exception as exc:
                        exc_str = str(exc).lower()
                        if "duplicate" in exc_str or "1062" in exc_str or "unique" in exc_str:
                            # Another concurrent request already created this table.
                            table = await self.table_repository.get_by_number(table_number)
                            if not table:
                                raise ValidationException(
                                    f"No se pudo crear ni encontrar la mesa {table_number}"
                                ) from exc
                        else:
                            raise
        if not table:
            raise ValidationException("Debe indicar una mesa válida")

        items_data = items_data or []
        if not items_data:
            raise ValidationException("El pedido debe tener al menos un plato")

        order_items = []
        total_amount = 0
        for item_data in items_data:
            dish = await self.dish_repository.get_by_id(item_data.get("dish_id"))
            if not dish:
                raise ValidationException(f"Plato con ID {item_data.get('dish_id')} no encontrado")
            if not dish.is_available:
                raise ValidationException(f"El plato '{dish.name}' está AGOTADO y no puede agregarse al pedido")
            quantity = item_data.get("quantity", 1)
            if quantity <= 0:
                raise ValidationException("La cantidad debe ser mayor a 0")

            item_total = dish.price * quantity
            total_amount += item_total
            order_items.append({
                "dish_id": dish.id,
                "dish_name": dish.name,
                "quantity": quantity,
                "unit_price": dish.price,
                "special_notes": item_data.get("special_notes"),
                "status": OrderItemStatus.PENDIENTE.value,
            })

        # Lógica de reinicio diario 22:00 America/Bogota
        cycle_key, _ = _get_cycle_for_timestamp()
        # Obtiene el siguiente daily_number para el ciclo actual (con manejo de concurrencia vía constraint)
        # Intenta hasta 3 veces en caso de colisión por concurrencia
        daily_number = 1
        try:
            # Cuenta órdenes en el ciclo actual
            # Usa el repositorio para contar; si el método no existe, fallback a 1
            if hasattr(self.order_repository, 'get_max_daily_number'):
                max_num = await self.order_repository.get_max_daily_number(cycle_key)
                daily_number = (max_num or 0) + 1
            else:
                # Fallback: lista y cuenta (menos eficiente pero funciona)
                existing = await self.order_repository.list_by_cycle(cycle_key) if hasattr(self.order_repository, 'list_by_cycle') else []
                daily_number = len(existing) + 1
        except Exception:
            daily_number = 1

        order = Order(
            table_id=table.id,
            camarero_id=camarero_id,
            status=OrderStatus.PENDIENTE.value,
            total_amount=total_amount,
            notes=notes,
            daily_number=daily_number,
            cycle_key=cycle_key,
            created_by=created_by,
        )
        for item_data in order_items:
            order.items.append(OrderItem(
                dish_id=item_data["dish_id"],
                dish_name=item_data.get("dish_name"),
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                status=item_data["status"],
                special_notes=item_data.get("special_notes"),
                created_by=created_by,
            ))

        created_order = await self.order_repository.create(order)
        # Notificación eliminada (rol suprimido)
        # Si se requiere notificar, se haría a ADMIN, pero se omite para no mantener lógica exclusiva de cocinero
        return created_order


class GetOrdersByCamareroUseCase:
    """Get only orders created by a specific waiter."""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, camarero_id: int, skip: int = 0, limit: int = 100) -> list[Order]:
        return await self.order_repository.get_by_camarero_id(camarero_id, skip, limit)


class GetKitchenOrdersUseCase:
    """Get orders relevant to the kitchen workflow."""
    
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
    
    async def execute(self, skip: int = 0, limit: int = 100) -> list[Order]:
        orders: list[Order] = []
        for state in (OrderStatus.PENDIENTE.value, OrderStatus.NUEVO.value, OrderStatus.EN_COCINA.value, OrderStatus.COMPLETADO.value):
            orders.extend(await self.order_repository.get_by_status(state, 0, limit))
        orders.sort(key=lambda order: order.created_at or datetime.min)
        return orders[skip: skip + limit]


class GetPendingOrdersForCajeroUseCase:
    """Get pending orders for CAJERO - only current cycle (America/Bogota 22:00)."""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, skip: int = 0, limit: int = 100) -> list[Order]:
        cycle_key, _ = _get_cycle_for_timestamp()
        # Use repository method that filters by cycle and pending statuses
        if hasattr(self.order_repository, 'get_pending_for_cajero'):
            return await self.order_repository.get_pending_for_cajero(cycle_key, skip, limit)
        # Fallback: filter in memory
        orders = await self.order_repository.list_by_cycle(cycle_key) if hasattr(self.order_repository, 'list_by_cycle') else await self.order_repository.list(0, 100)
        pending_statuses = {OrderStatus.PENDIENTE.value, OrderStatus.NUEVO.value}
        filtered = [o for o in orders if o.status in pending_statuses]
        filtered.sort(key=lambda o: o.created_at or datetime.min)
        return filtered[skip: skip + limit]


class GetEntregadosForCajeroUseCase:
    """Get ENTREGADO orders for CAJERO - current cycle."""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, skip: int = 0, limit: int = 100) -> list[Order]:
        cycle_key, _ = _get_cycle_for_timestamp()
        if hasattr(self.order_repository, 'get_entregados_for_cajero'):
            return await self.order_repository.get_entregados_for_cajero(cycle_key, skip, limit)
        orders = await self.order_repository.list_by_cycle(cycle_key) if hasattr(self.order_repository, 'list_by_cycle') else await self.order_repository.list(0, 100)
        filtered = [o for o in orders if o.status == OrderStatus.ENTREGADO.value]
        filtered.sort(key=lambda o: o.created_at or datetime.min)
        return filtered[skip: skip + limit]


class GetSalesReportUseCase:
    """Get sales report (PAGADO only) with filters."""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, start_date=None, end_date=None, dish_id=None, camarero_id=None, skip: int = 0, limit: int = 100) -> dict:
        if hasattr(self.order_repository, 'get_sales_aggregation'):
            agg = await self.order_repository.get_sales_aggregation(start_date, end_date, dish_id, camarero_id)
            orders = agg.get("orders", [])
            agg["orders"] = orders[skip: skip+limit] if limit else orders
            return agg
        orders = await self.order_repository.get_pagado_orders_filtered(start_date, end_date, dish_id, camarero_id, skip, limit)
        total_sales = sum(o.total_amount or 0 for o in orders)
        total_dishes = sum(sum(it.quantity for it in o.items) for o in orders)
        per_dish = {}
        for o in orders:
            for it in o.items:
                if dish_id and it.dish_id != dish_id:
                    continue
                per_dish.setdefault(it.dish_id, {"dish_id": it.dish_id, "dish_name": it.dish_name or f"Plato #{it.dish_id}", "quantity": 0, "total_cents": 0})
                per_dish[it.dish_id]["quantity"] += it.quantity
                per_dish[it.dish_id]["total_cents"] += it.unit_price * it.quantity
        return {
            "num_orders_pagadas": len(orders),
            "total_platos_vendidos": total_dishes,
            "total_ventas_cents": total_sales,
            "total_ventas_formatted": f"${total_sales/100:.2f}",
            "platos": sorted(per_dish.values(), key=lambda x: x["quantity"], reverse=True),
            "orders": orders
        }


class UpdateOrderForMeseroUseCase:
    """Allow mesero to edit their pending order (items/notes) before it is completed."""

    def __init__(self, order_repository: OrderRepository, dish_repository: DishRepository):
        self.order_repository = order_repository
        self.dish_repository = dish_repository

    async def execute(self, order_id: int, camarero_id: int, items_data: Optional[list[dict]] = None, notes: Optional[str] = None, updated_by: Optional[int] = None) -> Order:
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValidationException("Pedido no encontrado")
        if order.camarero_id != camarero_id:
            raise ConflictException("Solo puedes editar tus propios pedidos")
        if order.status not in (OrderStatus.PENDIENTE.value, OrderStatus.NUEVO.value):
            raise ConflictException("Solo se pueden editar pedidos PENDIENTES")
        # Validate items if provided
        if items_data is not None:
            if not items_data:
                raise ValidationException("El pedido debe tener al menos un plato")
            new_items = []
            total = 0
            for item_data in items_data:
                dish = await self.dish_repository.get_by_id(item_data.get("dish_id"))
                if not dish:
                    raise ValidationException(f"Plato con ID {item_data.get('dish_id')} no encontrado")
                if not dish.is_available:
                    raise ValidationException(f"El plato '{dish.name}' está AGOTADO")
                qty = item_data.get("quantity", 1)
                if qty <= 0:
                    raise ValidationException("La cantidad debe ser mayor a 0")
                total += dish.price * qty
                new_items.append({
                    "dish_id": dish.id,
                    "dish_name": dish.name,
                    "quantity": qty,
                    "unit_price": dish.price,
                    "special_notes": item_data.get("special_notes"),
                    "status": OrderItemStatus.PENDIENTE.value,
                })
            # Replace items via repository
            order = await self.order_repository.update_with_items(order_id, new_items, total, notes, updated_by)
        elif notes is not None:
            order.notes = notes
            order.updated_by = updated_by
            order = await self.order_repository.update(order_id, order)
        return order


class GetOrderUseCase:
    """Use case for getting order information."""
    
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
    
    async def execute(self, order_id: int) -> Order:
        """Get order by ID."""
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValidationException("Pedido no encontrado")
        return order


class ListOrdersUseCase:
    """Use case for listing orders."""
    
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
    
    async def execute(self, skip: int = 0, limit: int = 10) -> list[Order]:
        """List orders."""
        return await self.order_repository.list(skip, limit)


class UpdateOrderStatusUseCase:
    """Use case for updating order status - strict workflow: PENDIENTE->EN_COCINA->ENTREGADO->PAGADO and CANCELADO."""

    ALLOWED_TRANSITIONS = {
        OrderStatus.PENDIENTE.value: {OrderStatus.EN_COCINA.value, OrderStatus.CANCELADO.value},
        OrderStatus.NUEVO.value: {OrderStatus.EN_COCINA.value, OrderStatus.CANCELADO.value},
        OrderStatus.EN_COCINA.value: {OrderStatus.ENTREGADO.value, OrderStatus.CANCELADO.value},
        OrderStatus.COMPLETADO.value: {OrderStatus.ENTREGADO.value},
        OrderStatus.ENTREGADO.value: {OrderStatus.PAGADO.value},
        OrderStatus.CANCELADO.value: set(),
        OrderStatus.PAGADO.value: set(),
    }

    async def _check_role_permission(self, order: Order, current_status: str, target_status: str, role: str, updated_by: int):
        if target_status == OrderStatus.EN_COCINA.value:
            if role not in ("CAJERO", "ADMIN", "MONITOR"):
                raise ConflictException("Solo el cajero o el monitor pueden enviar pedidos a cocina mediante impresión")
        elif target_status == OrderStatus.CANCELADO.value:
            if role == "CAMARERO" and order.camarero_id != updated_by:
                raise ConflictException("El mesero solo puede cancelar pedidos que él creó")
            if role not in ("CAMARERO", "ADMIN"):
                raise ConflictException("Solo el mesero puede cancelar pedidos")
            if current_status not in (OrderStatus.PENDIENTE.value, OrderStatus.NUEVO.value, OrderStatus.EN_COCINA.value):
                raise ConflictException("Solo se pueden cancelar pedidos PENDIENTE o EN_COCINA")
        elif target_status == OrderStatus.ENTREGADO.value:
            if role not in ("ADMIN",):
                raise ConflictException("Solo el administrador puede marcar pedidos como entregados")
            if current_status not in (OrderStatus.EN_COCINA.value, OrderStatus.COMPLETADO.value):
                raise ConflictException("Solo se pueden entregar pedidos que estén EN COCINA")
        elif target_status == OrderStatus.PAGADO.value:
            if role not in ("CAJERO", "ADMIN"):
                raise ConflictException("Solo el cajero puede marcar pedidos como pagados")
            if current_status != OrderStatus.ENTREGADO.value:
                raise ConflictException("Solo se pueden pagar pedidos que estén ENTREGADO")
        elif target_status == OrderStatus.COMPLETADO.value:
            raise ConflictException("El estado COMPLETADO ya no es válido en el flujo actual. Use EN_COCINA/ENTREGADO/PAGADO")
        else:
            raise ConflictException(f"Transición no permitida: {current_status} -> {target_status}")

    def __init__(self, order_repository: OrderRepository, notification_repository: NotificationRepository):
        self.order_repository = order_repository
        self.notification_repository = notification_repository

    async def execute(self, order_id: int, status: str, updated_by: Optional[int] = None, role: Optional[str] = None) -> Order:
        """Update order status while enforcing strict workflow."""
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValidationException("Pedido no encontrado")
        valid_statuses = [s.value for s in OrderStatus]
        if status not in valid_statuses:
            raise ValidationException(f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}")
        current_status = order.status
        if current_status in (OrderStatus.PAGADO.value, OrderStatus.CANCELADO.value):
            raise ConflictException(f"No se puede modificar un pedido que ya está {current_status}")
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, set())
        if status not in allowed:
            raise ConflictException(f"Transición no permitida: {current_status} → {status}. Transiciones válidas desde {current_status}: {', '.join(sorted(allowed)) if allowed else 'ninguna (terminal)'}")
        await self._check_role_permission(order, current_status, status, role or "", updated_by)
        if status == OrderStatus.EN_COCINA.value and not order.started_at:
            OrderService.start_order(order)
        elif status == OrderStatus.ENTREGADO.value and not order.delivered_at:
            OrderService.deliver_order(order)
        elif status == OrderStatus.PAGADO.value:
            OrderService.pay_order(order)
        elif status == OrderStatus.CANCELADO.value:
            pass
        order.status = status
        order.updated_by = updated_by
        updated_order = await self.order_repository.update(order_id, order)
        if status == OrderStatus.EN_COCINA.value:
            try:
                notification = Notification(
                    order_id=order_id,
                    event_type=NotificationEvent.PEDIDO_COMPLETADO.value,
                    target_role="CAMARERO",
                    message=f"Pedido #{order_id} enviado a cocina",
                    created_by=updated_by,
                )
                await self.notification_repository.create(notification)
            except Exception:
                pass
        return updated_order


class DeleteOrderUseCase:
    """Use case for deleting order."""
    
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
    
    async def execute(self, order_id: int) -> bool:
        """Delete order."""
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValidationException("Pedido no encontrado")
        return await self.order_repository.delete(order_id)


class GetOrdersByStatusUseCase:
    """Use case for getting orders by status."""
    
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
    
    async def execute(self, status: str, skip: int = 0, limit: int = 10) -> list[Order]:
        """Get orders by status."""
        valid_statuses = [s.value for s in OrderStatus]
        if status not in valid_statuses:
            raise ValidationException(f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}")
        
        return await self.order_repository.get_by_status(status, skip, limit)


class GetOrderByTableUseCase:
    """Use case for getting active order for table."""
    
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
    
    async def execute(self, table_id: int) -> Optional[Order]:
        """Get active order for table."""
        return await self.order_repository.get_by_table_id(table_id)


class UpdateOrderItemStatusUseCase:
    """Use case for updating order item status."""
    
    def __init__(self, order_item_repository: OrderItemRepository, notification_repository: NotificationRepository):
        self.order_item_repository = order_item_repository
        self.notification_repository = notification_repository
    
    async def execute(self, item_id: int, status: str, updated_by: Optional[int] = None) -> OrderItem:
        """Update order item status."""
        item = await self.order_item_repository.get_by_id(item_id)
        if not item:
            raise ValidationException("Item de pedido no encontrado")
        
        # Validate status
        valid_statuses = [s.value for s in OrderItemStatus]
        if status not in valid_statuses:
            raise ValidationException(f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}")
        
        # Update timestamps
        if status == OrderItemStatus.EN_PREPARACION.value and not item.started_at:
            OrderItemService.start_item(item)
        elif status == OrderItemStatus.LISTO.value and not item.completed_at:
            OrderItemService.complete_item(item)
        
        item.status = status
        item.updated_by = updated_by
        
        updated_item = await self.order_item_repository.update(item_id, item)
        
        # Create notification when item is ready
        if status == OrderItemStatus.LISTO.value:
            notification = Notification(
                order_id=item.order_id,
                event_type=NotificationEvent.PLATO_LISTO.value,
                target_role="CAMARERO",
                message=f"Plato listo en el pedido #{item.order_id}",
                created_by=updated_by,
            )
            await self.notification_repository.create(notification)
        
        return updated_item
