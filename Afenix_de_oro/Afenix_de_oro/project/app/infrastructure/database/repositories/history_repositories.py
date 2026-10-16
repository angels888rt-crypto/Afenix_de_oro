"""History / audit log repository."""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import HistoryLogModel
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    try:
        BOGOTA_TZ = ZoneInfo("America/Bogota")
    except Exception:
        BOGOTA_TZ = timezone(timedelta(hours=-5))
except ImportError:
    BOGOTA_TZ = timezone(timedelta(hours=-5))  # type: ignore


class HistoryRepository:
    """Repository for history_logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        category: str,
        action: str,
        description: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        details: Optional[dict] = None,
        performed_by: Optional[int] = None,
        performed_by_username: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """Create a history log entry."""
        model = HistoryLogModel(
            category=category,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            performed_by=performed_by,
            performed_by_username=performed_by_username,
            created_at=created_at or datetime.now(timezone.utc),
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_dict(model)

    async def list(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> list[dict]:
        """List history logs with optional filters."""
        stmt = select(HistoryLogModel).order_by(HistoryLogModel.created_at.desc())
        if category and category != "ALL":
            # Normalize
            cat = category.upper()
            if cat == "RECENT" or cat == "GENERAL":
                # Recent is handled separately, but if passed here treat as ALL with date filter
                pass
            else:
                stmt = stmt.where(HistoryLogModel.category == cat)
        if since:
            stmt = stmt.where(HistoryLogModel.created_at >= since)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(r) for r in rows]

    async def list_recent(self, days: int = 2, skip: int = 0, limit: int = 100) -> list[dict]:
        """List recent history (last N days) across all categories, most recent first."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(HistoryLogModel)
            .where(HistoryLogModel.created_at >= cutoff)
            .order_by(HistoryLogModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(r) for r in rows]

    async def delete_older_than(self, days: int = 4) -> int:
        """Delete history logs older than `days`. Returns number deleted.
        Uses UTC comparison; `days` is retention period.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(HistoryLogModel).where(HistoryLogModel.created_at < cutoff)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount or 0

    @staticmethod
    def _to_dict(model: HistoryLogModel) -> dict:
        details = None
        if model.details:
            try:
                details = json.loads(model.details)
            except Exception:
                details = model.details
        return {
            "id": model.id,
            "category": model.category,
            "action": model.action,
            "entity_type": model.entity_type,
            "entity_id": model.entity_id,
            "entity_name": model.entity_name,
            "description": model.description,
            "details": details,
            "performed_by": model.performed_by,
            "performed_by_username": model.performed_by_username,
            "created_at": model.created_at,
        }

    @staticmethod
    def now_bogota() -> datetime:
        """Return current time in America/Bogota."""
        if BOGOTA_TZ:
            return datetime.now(BOGOTA_TZ)
        return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5)))

    @staticmethod
    def seconds_until_next_6am_bogota() -> float:
        """Compute seconds until next 06:00 America/Bogota."""
        now = HistoryRepository.now_bogota()
        next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run + timedelta(days=1)
        delta = (next_run - now).total_seconds()
        return max(delta, 0.0)
