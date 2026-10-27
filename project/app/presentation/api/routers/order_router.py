"""Order API routers and role-aware order workflow."""
from fastapi import APIRouter, Depends, status, Query, HTTPException

from app.infrastructure.database.repositories import (
    OrderRepository, OrderItemRepository, DishRepository, NotificationRepository,
    TableRepository
)
from app.application.use_cases.order_use_cases import (
    CreateOrderUseCase, GetOrderUseCase, ListOrdersUseCase, UpdateOrderStatusUseCase,
    DeleteOrderUseCase, GetOrdersByStatusUseCase, GetOrderByTableUseCase,
    UpdateOrderItemStatusUseCase, GetOrdersByCamareroUseCase, GetKitchenOrdersUseCase,
    GetPendingOrdersForCajeroUseCase, UpdateOrderForMeseroUseCase,
    GetEntregadosForCajeroUseCase, GetSalesReportUseCase
)
from app.application.dto import (
    OrderCreateRequest, OrderUpdateRequest, OrderResponse, OrderItemUpdateRequest,
    OrderItemResponse, OrderEditRequest
)
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_order_repository, get_order_item_repository, get_dish_repository,
    get_notification_repository, get_table_repository, get_current_user, require_role, get_history_repository
)
from app.infrastructure.database.repositories import HistoryRepository

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


async def _log_history_safe(repo: HistoryRepository, **kwargs):
    try:
        await repo.create(**kwargs)
    except Exception:
        pass

def _to_response(order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        table_id=order.table_id,
        table_number=getattr(order, 'table_number', None),
        camarero_id=order.camarero_id,
        status=order.status,
        total_amount=order.total_amount,
        notes=order.notes,
        items=[
            OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                dish_id=item.dish_id,
                dish_name=getattr(item, "dish_name", None),
                quantity=item.quantity,
                unit_price=item.unit_price,
                status=item.status,
                special_notes=item.special_notes,
                started_at=item.started_at,
                completed_at=item.completed_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in order.items
        ],
        daily_number=getattr(order, 'daily_number', None),
        cycle_key=getattr(order, 'cycle_key', None),
        started_at=order.started_at,
        completed_at=order.completed_at,
        delivered_at=order.delivered_at,
        paid_at=getattr(order, 'paid_at', None),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("", response_model=ResponseSchema[OrderResponse], status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
    dish_repository: DishRepository = Depends(get_dish_repository),
    table_repository: TableRepository = Depends(get_table_repository),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Create a new order. Allowed for camareros (and admins)."""
    current_user = await require_role("CAMARERO", "ADMIN")(current_user)
    use_case = CreateOrderUseCase(order_repository, dish_repository, table_repository, notification_repository)
    order = await use_case.execute(
        table_id=request.table_id,
        table_number=request.table_number,
        items_data=[item.model_dump() for item in request.items],
        notes=request.notes,
        camarero_id=current_user["user_id"] if current_user["role"] == "CAMARERO" else current_user["user_id"],
        created_by=current_user["user_id"],
    )
    # Display uses daily_number and table_number (correct Mesa)
    disp_num = getattr(order, 'daily_number', None) or order.id
    disp_mesa = getattr(order, 'table_number', None) or order.table_id
    await _log_history_safe(
        history_repo,
        category="ORDENES",
        action="CREADO",
        entity_type="ORDEN",
        entity_id=order.id,
        entity_name=f"Orden #{disp_num} Mesa {disp_mesa}",
        description=f"Orden #{disp_num} creada para mesa {disp_mesa} (total ${order.total_amount/100:.2f}, {len(order.items)} platos)",
        details={"order_id": order.id, "daily_number": disp_num, "table_id": order.table_id, "table_number": disp_mesa, "total": order.total_amount, "items": len(order.items), "status": order.status},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
    return ResponseSchema(success=True, message="Pedido creado exitosamente", data=_to_response(order))


# Specific collection routes come before /{order_id} to avoid route conflicts.
@router.get("/mine", response_model=ResponseSchema[list[OrderResponse]])
async def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get only the orders created by the authenticated waiter."""
    await require_role("CAMARERO")(current_user)
    use_case = GetOrdersByCamareroUseCase(order_repository)
    orders = await use_case.execute(current_user["user_id"], skip, limit)
    return ResponseSchema(
        success=True,
        message="Pedidos del mesero obtenidos exitosamente",
        data=[_to_response(order) for order in orders],
    )


@router.get("/kitchen", response_model=ResponseSchema[list[OrderResponse]])
async def get_kitchen_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get orders visible to kitchen (ADMIN and MONITOR)."""
    await require_role("ADMIN", "MONITOR")(current_user)
    use_case = GetKitchenOrdersUseCase(order_repository)
    orders = await use_case.execute(skip, limit)
    return ResponseSchema(
        success=True,
        message="Pedidos de cocina obtenidos exitosamente",
        data=[_to_response(order) for order in orders],
    )


@router.get("/monitor/pending", response_model=ResponseSchema[list[OrderResponse]])
async def get_monitor_pending(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get pending orders for kitchen monitor (MONITOR and ADMIN)."""
    await require_role("MONITOR", "ADMIN")(current_user)
    use_case = GetKitchenOrdersUseCase(order_repository)
    orders = await use_case.execute(skip, limit)
    return ResponseSchema(
        success=True,
        message="Órdenes pendientes para monitor obtenidas exitosamente",
        data=[_to_response(order) for order in orders],
    )


@router.get("/cajero/pending", response_model=ResponseSchema[list[OrderResponse]])
async def get_cajero_pending_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get pending orders for CAJERO - only current cycle (America/Bogota 22:00)."""
    await require_role("CAJERO", "ADMIN")(current_user)
    use_case = GetPendingOrdersForCajeroUseCase(order_repository)
    orders = await use_case.execute(skip, limit)
    return ResponseSchema(success=True, message="Pedidos pendientes obtenidos exitosamente", data=[_to_response(o) for o in orders])


@router.get("/cajero/entregados", response_model=ResponseSchema[list[OrderResponse]])
async def get_cajero_entregados(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get ENTREGADO orders for CAJERO - pestaña Entregados (solo ciclo actual)."""
    await require_role("CAJERO", "ADMIN")(current_user)
    use_case = GetEntregadosForCajeroUseCase(order_repository)
    orders = await use_case.execute(skip, limit)
    return ResponseSchema(success=True, message="Pedidos entregados obtenidos exitosamente", data=[_to_response(o) for o in orders])


@router.get("/reports/sales", response_model=ResponseSchema[dict])
async def get_sales_report(
    start_date: str = Query(None, description="Fecha inicio YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha fin YYYY-MM-DD"),
    date: str = Query(None, description="Fecha específica YYYY-MM-DD"),
    dish_id: int = Query(None, ge=1),
    camarero_id: int = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Reporte de ventas: solo órdenes PAGADO con filtros combinable por fecha/plato/mesero."""
    await require_role("CAJERO", "ADMIN")(current_user)
    from datetime import datetime, timezone, timedelta
    s_dt = None
    e_dt = None
    try:
        from zoneinfo import ZoneInfo
        BOGOTA_TZ = ZoneInfo("America/Bogota")
    except Exception:
        BOGOTA_TZ = timezone(timedelta(hours=-5))
    def _parse_day(d: str):
        dt_local = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=BOGOTA_TZ)
        start_utc = dt_local.astimezone(timezone.utc)
        end_utc = (dt_local + timedelta(days=1) - timedelta(seconds=1)).astimezone(timezone.utc)
        return start_utc, end_utc
    if date:
        try:
            s_dt, e_dt = _parse_day(date)
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    else:
        if start_date:
            try:
                s_dt, _ = _parse_day(start_date)
            except Exception:
                try:
                    s_dt = datetime.fromisoformat(start_date.replace('Z','+00:00'))
                    if s_dt.tzinfo is None:
                        s_dt = s_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    raise HTTPException(status_code=400, detail="start_date inválido")
        if end_date:
            try:
                _, e_dt = _parse_day(end_date)
            except Exception:
                try:
                    e_dt = datetime.fromisoformat(end_date.replace('Z','+00:00'))
                    if e_dt.tzinfo is None:
                        e_dt = e_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    raise HTTPException(status_code=400, detail="end_date inválido")
    use_case = GetSalesReportUseCase(order_repository)
    data = await use_case.execute(start_date=s_dt, end_date=e_dt, dish_id=dish_id, camarero_id=camarero_id, skip=skip, limit=limit)
    orders_resp = [_to_response(o).model_dump() for o in data.get("orders", [])]
    platos = data.get("platos", [])
    for p in platos:
        p["total_formatted"] = f"${(p.get('total_cents',0)/100):.2f}"
    result = {
        "num_ordenes_pagadas": data.get("num_orders_pagadas", 0),
        "total_platos_vendidos": data.get("total_platos_vendidos", 0),
        "total_ventas_cents": data.get("total_ventas_cents", 0),
        "total_ventas": data.get("total_ventas_cents", 0)/100,
        "total_ventas_formatted": data.get("total_ventas_formatted", "$0.00"),
        "platos": platos,
        "orders": orders_resp,
        "orders_count": len(orders_resp),
    }
    return ResponseSchema(success=True, message="Reporte de ventas obtenido", data=result)


@router.get("/history", response_model=ResponseSchema[list[OrderResponse]])
async def get_order_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get the complete order history. Admin only."""
    await require_role("ADMIN")(current_user)
    orders = await order_repository.list(skip, limit)
    return ResponseSchema(
        success=True,
        message="Historial de órdenes obtenido exitosamente",
        data=[_to_response(order) for order in orders],
    )


@router.get("/status/{status}", response_model=ResponseSchema[list[OrderResponse]])
async def get_orders_by_status(
    status: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get orders by status. Restricted to admin."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = GetOrdersByStatusUseCase(order_repository)
    orders = await use_case.execute(status, skip, limit)
    return ResponseSchema(success=True, message="Pedidos obtenidos exitosamente", data=[_to_response(o) for o in orders])


@router.get("/table/{table_id}/active", response_model=ResponseSchema[OrderResponse])
async def get_order_by_table(
    table_id: int,
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Get active order for table."""
    await require_role("CAMARERO", "ADMIN")(current_user)
    use_case = GetOrderByTableUseCase(order_repository)
    order = await use_case.execute(table_id)
    if not order:
        from app.shared.exceptions import ResourceNotFoundException
        raise ResourceNotFoundException("No hay pedido activo para esta mesa")
    return ResponseSchema(success=True, message="Pedido obtenido exitosamente", data=_to_response(order))




@router.get("", response_model=ResponseSchema[list[OrderResponse]])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """List all orders for admin only; use /mine or /kitchen for operational views."""
    await require_role("ADMIN")(current_user)
    use_case = ListOrdersUseCase(order_repository)
    orders = await use_case.execute(skip, limit)
    return ResponseSchema(success=True, message="Pedidos obtenidos exitosamente", data=[_to_response(o) for o in orders])


@router.put("/{order_id}/edit", response_model=ResponseSchema[OrderResponse])
async def edit_order(
    order_id: int,
    request: OrderEditRequest,
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
    dish_repository: DishRepository = Depends(get_dish_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Edit pending order - mesero can modify his own PENDIENTE orders."""
    await require_role("CAMARERO")(current_user)
    use_case = UpdateOrderForMeseroUseCase(order_repository, dish_repository)
    try:
        order = await use_case.execute(
            order_id=order_id,
            camarero_id=current_user["user_id"],
            items_data=[item.model_dump() for item in request.items],
            notes=request.notes,
            updated_by=current_user["user_id"],
        )
    except Exception as exc:
        from app.shared.exceptions import ConflictException, ValidationException
        if isinstance(exc, (ConflictException, ValidationException)):
            raise HTTPException(status_code=409 if isinstance(exc, ConflictException) else 400, detail=str(exc)) from exc
        raise
    disp_num = getattr(order, 'daily_number', None) or order.id
    disp_mesa = getattr(order, 'table_number', None) or order.table_id
    await _log_history_safe(
        history_repo,
        category="ORDENES",
        action="ACTUALIZADO",
        entity_type="ORDEN",
        entity_id=order.id,
        entity_name=f"Orden #{disp_num} Mesa {disp_mesa}",
        description=f"Orden #{disp_num} editada por mesero {current_user.get('username')} (mesa {disp_mesa})",
        details={"order_id": order.id, "daily_number": disp_num, "items": len(order.items), "total": order.total_amount},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
    return ResponseSchema(success=True, message="Pedido actualizado exitosamente", data=_to_response(order))


@router.put("/items/{item_id}", response_model=ResponseSchema[OrderItemResponse])
async def update_order_item_status(
    item_id: int,
    request: OrderItemUpdateRequest,
    current_user: dict = Depends(get_current_user),
    order_item_repository: OrderItemRepository = Depends(get_order_item_repository),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
):
    """Update order item status (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = UpdateOrderItemStatusUseCase(order_item_repository, notification_repository)
    item = await use_case.execute(item_id=item_id, status=request.status, updated_by=current_user["user_id"])
    return ResponseSchema(
        success=True,
        message="Item actualizado exitosamente",
        data=OrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            dish_id=item.dish_id,
            dish_name=getattr(item, "dish_name", None),
            quantity=item.quantity,
            unit_price=item.unit_price,
            status=item.status,
            special_notes=item.special_notes,
            started_at=item.started_at,
            completed_at=item.completed_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ),
    )

@router.put("/{order_id}", response_model=ResponseSchema[OrderResponse])
async def update_order_status(
    order_id: int,
    request: OrderUpdateRequest,
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
    notification_repository: NotificationRepository = Depends(get_notification_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Role-aware order transition: admin completes, waiter delivers."""
    if not request.status:
        raise HTTPException(status_code=400, detail="Debe indicar el nuevo estado del pedido")

    target = request.status.upper()
    order = await order_repository.get_by_id(order_id)
    if not order:
        from app.shared.exceptions import ValidationException
        raise ValidationException("Pedido no encontrado")

    if current_user["role"] not in ("ADMIN", "CAMARERO", "CAJERO"):
        raise HTTPException(status_code=403, detail="Rol no autorizado")

    prev_status = order.status
    use_case = UpdateOrderStatusUseCase(order_repository, notification_repository)
    try:
        updated = await use_case.execute(
            order_id=order_id,
            status=target,
            updated_by=current_user["user_id"],
            role=current_user["role"],
        )
    except Exception as exc:
        # Preserve the project's domain exceptions while exposing the correct HTTP status.
        from app.shared.exceptions import ConflictException
        if isinstance(exc, ConflictException):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise
    await _log_history_safe(
        history_repo,
        category="ORDENES",
        action="ACTUALIZADO",
        entity_type="ORDEN",
        entity_id=order_id,
        entity_name=f"Orden #{order_id}",
        description=f"Orden #{order_id} actualizada: {prev_status} → {target} por {current_user.get('username')}",
        details={"order_id": order_id, "from": prev_status, "to": target},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
    return ResponseSchema(success=True, message="Pedido actualizado exitosamente", data=_to_response(updated))


@router.post("/cleanup/daily", response_model=ResponseSchema[dict])
async def cleanup_orders_daily(
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
):
    """Manual trigger for 22:00 Bogota daily cleanup (ADMIN only) — borra todos los pedidos visibles en mesero-pedidos."""
    await require_role("ADMIN")(current_user)
    deleted = await order_repository.delete_all()
    return ResponseSchema(success=True, message=f"Limpieza diaria ejecutada: {deleted} pedidos eliminados", data={"deleted": deleted})


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Delete order (admin only)."""
    await require_role("ADMIN")(current_user)
    order_before = await order_repository.get_by_id(order_id)
    use_case = DeleteOrderUseCase(order_repository)
    await use_case.execute(order_id)
    await _log_history_safe(
        history_repo,
        category="ORDENES",
        action="ELIMINADO",
        entity_type="ORDEN",
        entity_id=order_id,
        entity_name=f"Orden #{order_id}" if not order_before else f"Orden #{order_id} Mesa {order_before.table_id}",
        description=f"Orden #{order_id} eliminada por {current_user.get('username')}",
        details={"order_id": order_id},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
