"""History API router — admin-historial filters and retention."""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.infrastructure.database.repositories import HistoryRepository
from app.application.dto import HistoryResponse
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_history_repository, get_current_user, require_role
)

router = APIRouter(prefix="/api/v1/history", tags=["History"])


@router.get("", response_model=ResponseSchema[list[HistoryResponse]])
async def list_history(
    category: Optional[str] = Query(None, description="ORDENES, PLATOS, LOGIN, USUARIOS, ALL, RECENT"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    days: Optional[int] = Query(None, ge=1, le=30, description="Filter by last N days"),
    current_user: dict = Depends(get_current_user),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """List history logs with filters.

    Categories:
    - ORDENES: creación, actualización y eliminación de órdenes
    - PLATOS: platos creados, actualizados y eliminados
    - LOGIN: registros de inicios de sesión (usuarios ingresados)
    - USUARIOS: usuarios creados, actualizados y eliminados
    - RECENT / GENERAL: historial más reciente (últimos 2 días, todas las categorías)

    Requires ADMIN role.
    """
    await require_role("ADMIN")(current_user)

    cat = (category or "ALL").upper().strip()

    # Recent general: last ~2 days across all categories, sorted most recent first
    if cat in ("RECENT", "RECIENTE", "GENERAL", "HISTORIAL_RECIENTE"):
        effective_days = days or 2
        logs = await history_repo.list_recent(days=effective_days, skip=skip, limit=limit)
        return ResponseSchema(success=True, message="Historial reciente obtenido", data=[HistoryResponse(**l) for l in logs])

    # Support "RECIENTE" with implicit days filter
    if days:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        logs = await history_repo.list(category=cat if cat != "ALL" else None, skip=skip, limit=limit, since=cutoff)
    else:
        if cat == "ALL":
            logs = await history_repo.list(category=None, skip=skip, limit=limit)
        else:
            # Validate category
            valid = {"ORDENES", "PLATOS", "LOGIN", "USUARIOS"}
            if cat not in valid:
                # Allow friendly names: ordenes->ORDENES etc
                mapping = {"ORDENES": "ORDENES", "ORDEN": "ORDENES", "PLATOS": "PLATOS", "PLATO": "PLATOS", "LOGIN": "LOGIN", "INGRESOS": "LOGIN", "USUARIOS_INGRESADOS": "LOGIN", "USUARIOS": "USUARIOS", "USUARIO": "USUARIOS"}
                cat = mapping.get(cat, cat)
            logs = await history_repo.list(category=cat, skip=skip, limit=limit)

    return ResponseSchema(success=True, message="Historial obtenido", data=[HistoryResponse(**l) for l in logs])


@router.delete("/cleanup", response_model=ResponseSchema[dict])
async def cleanup_history(
    days: int = Query(4, ge=1, description="Retention days, records older than this are deleted"),
    current_user: dict = Depends(get_current_user),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Manual cleanup of history older than `days` (default 4). Admin only.
    The automatic scheduled cleanup runs daily at 06:00 America/Bogota without needing this endpoint.
    """
    await require_role("ADMIN")(current_user)
    deleted = await history_repo.delete_older_than(days=days)
    return ResponseSchema(success=True, message=f"Limpieza completada: {deleted} registros eliminados", data={"deleted": deleted, "retention_days": days})


@router.get("/stats", response_model=ResponseSchema[dict])
async def history_stats(
    current_user: dict = Depends(get_current_user),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Return counts per category and retention info (admin only)."""
    await require_role("ADMIN")(current_user)
    # Simple stats: count per category by fetching
    from datetime import datetime, timedelta, timezone
    all_logs = await history_repo.list(category=None, skip=0, limit=1000)
    counts = {"ORDENES": 0, "PLATOS": 0, "LOGIN": 0, "USUARIOS": 0, "TOTAL": len(all_logs)}
    for l in all_logs:
        if l["category"] in counts:
            counts[l["category"]] += 1
    # Recent counts (2 days)
    cutoff_2d = datetime.now(timezone.utc) - timedelta(days=2)
    recent = [l for l in all_logs if l["created_at"] >= cutoff_2d]
    # Old records that would be deleted
    cutoff_4d = datetime.now(timezone.utc) - timedelta(days=4)
    old = [l for l in all_logs if l["created_at"] < cutoff_4d]
    return ResponseSchema(success=True, message="Estadísticas de historial", data={"counts": counts, "recent_2d": len(recent), "older_than_4d": len(old)})
