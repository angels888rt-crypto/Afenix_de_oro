"""Eliminación diaria de pedidos mesero-pedidos a las 22:00 America/Bogota."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    BOGOTA_TZ = ZoneInfo("America/Bogota")
except Exception:
    BOGOTA_TZ = timezone(timedelta(hours=-5))

logger = logging.getLogger(__name__)

def _now_bogota() -> datetime:
    return datetime.now(BOGOTA_TZ)

def seconds_until_next_22_bogota() -> float:
    """Segundos hasta el próximo 22:00 en America/Bogota."""
    now = _now_bogota()
    nxt = now.replace(hour=22, minute=0, second=0, microsecond=0)
    if nxt <= now:
        nxt += timedelta(days=1)
    return max((nxt - now).total_seconds(), 0)

async def _cleanup_orders_once() -> int:
    try:
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.database.repositories import OrderRepository
        async with AsyncSessionLocal() as session:
            repo = OrderRepository(session)
            deleted = await repo.delete_all()
            if deleted:
                logger.info(f"[OrderCleanup] Eliminados {deleted} pedidos a las 22:00 Bogota (mesero-pedidos).")
            else:
                logger.info("[OrderCleanup] 22:00 Bogota — 0 pedidos para eliminar.")
            return deleted
    except Exception as exc:
        logger.error(f"[OrderCleanup] Error en limpieza 22:00: {exc}")
        return 0

async def order_cleanup_loop() -> None:
    while True:
        secs = seconds_until_next_22_bogota()
        now_bog = _now_bogota().strftime("%Y-%m-%d %H:%M:%S %Z")
        nxt_bog = (_now_bogota() + timedelta(seconds=secs)).strftime("%Y-%m-%d %H:%M:%S %Z")
        logger.info(f"[OrderCleanup] Ahora Bogota: {now_bog} — próximo 22:00 Bogota: {nxt_bog} (en {int(secs)}s)")
        try:
            await asyncio.sleep(secs)
        except asyncio.CancelledError:
            logger.info("[OrderCleanup] Scheduler cancelado.")
            break
        await _cleanup_orders_once()

def start_order_cleanup_scheduler():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("[OrderCleanup] No hay event loop — scheduler no iniciado.")
        return None
    task = loop.create_task(order_cleanup_loop())
    logger.info("[OrderCleanup] Tarea programada creada (22:00 America/Bogota, borrado mesero-pedidos).")
    return task
