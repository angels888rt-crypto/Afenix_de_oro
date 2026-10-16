"""Automatic history cleanup scheduler — runs daily at 06:00 America/Bogota, retention 4 days."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    try:
        BOGOTA_TZ = ZoneInfo("America/Bogota")
    except Exception:  # pragma: no cover
        BOGOTA_TZ = timezone(timedelta(hours=-5))
except ImportError:  # pragma: no cover
    BOGOTA_TZ = timezone(timedelta(hours=-5))

logger = logging.getLogger(__name__)


def _now_bogota() -> datetime:
    return datetime.now(BOGOTA_TZ)


def seconds_until_next_6am_bogota() -> float:
    """Seconds until next 06:00 in America/Bogota timezone."""
    now = _now_bogota()
    next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return max((next_run - now).total_seconds(), 0)


async def _cleanup_once() -> int:
    """Delete history logs older than 4 days. Returns deleted count."""
    try:
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.database.repositories import HistoryRepository

        async with AsyncSessionLocal() as session:
            repo = HistoryRepository(session)
            deleted = await repo.delete_older_than(days=4)
            if deleted:
                logger.info(f"[HistoryCleanup] Eliminados {deleted} registros con >4 días (06:00 Bogota).")
            else:
                logger.info("[HistoryCleanup] Limpieza ejecutada a las 06:00 Bogota — 0 registros eliminados.")
            return deleted
    except Exception as exc:  # pragma: no cover
        logger.error(f"[HistoryCleanup] Error en limpieza programada: {exc}")
        return 0


async def history_cleanup_loop() -> None:
    """Background loop: wait until next 06:00 Bogota, clean, then every 24h."""
    # Run immediate cleanup on startup to catch overdue records
    logger.info("[HistoryCleanup] Scheduler iniciado — limpieza inicial al arrancar.")
    await _cleanup_once()

    while True:
        secs = seconds_until_next_6am_bogota()
        now_bog = _now_bogota().strftime("%Y-%m-%d %H:%M:%S %Z")
        next_bog = (_now_bogota() + timedelta(seconds=secs)).strftime("%Y-%m-%d %H:%M:%S %Z")
        logger.info(f"[HistoryCleanup] Ahora Bogota: {now_bog} — próximo 06:00 Bogota: {next_bog} (en {int(secs)}s)")
        try:
            await asyncio.sleep(secs)
        except asyncio.CancelledError:
            logger.info("[HistoryCleanup] Scheduler cancelado.")
            break
        await _cleanup_once()
        # After first run, sleep 24h minus small drift; but recalc to stay at 06:00
        # Loop continues and recomputes exact seconds to next 6am


def start_history_cleanup_scheduler():
    """Start background task for daily 06:00 Bogota cleanup. Call from FastAPI startup."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop (e.g., during tests); skip
        logger.warning("[HistoryCleanup] No running event loop — scheduler no iniciado.")
        return None
    task = loop.create_task(history_cleanup_loop())
    logger.info("[HistoryCleanup] Tarea programada creada (06:00 America/Bogota, retención 4 días).")
    return task
