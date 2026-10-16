from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.infrastructure.database.repositories.base_repositories import UserRepository


class DummyResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return self

    def first(self):
        return self._value


class DummySession:
    def __init__(self, db_user):
        self.db_user = db_user
        self.flush_calls = 0
        self.commit_calls = 0
        self.refresh_calls = 0

    async def execute(self, _stmt):
        return DummyResult(self.db_user)

    async def flush(self):
        self.flush_calls += 1

    async def commit(self):
        self.commit_calls += 1

    async def refresh(self, _obj):
        self.refresh_calls += 1


@pytest.mark.asyncio
async def test_user_repository_update_commits_and_refreshes() -> None:
    db_user = SimpleNamespace(
        id=1,
        username="old",
        email="old@example.com",
        password_hash="hash",
        full_name="Old Name",
        phone="123",
        is_active=True,
        role="CAMARERO",
        updated_at=None,
        updated_by=None,
        created_at=None,
        deleted_at=None,
        created_by=None,
    )
    session = DummySession(db_user)
    repo = UserRepository(session)
    repo.get_by_id = AsyncMock(return_value=object())

    user = SimpleNamespace(
        username="new",
        email="new@example.com",
        password_hash="newhash",
        full_name="New Name",
        phone="999",
        is_active=False,
        role="CAMARERO",
        updated_by=7,
    )

    result = await repo.update(1, user)

    assert result is not None
    assert db_user.username == "new"
    assert db_user.role == "CAMARERO"
    assert session.flush_calls == 1
    assert session.commit_calls == 1
    assert session.refresh_calls == 1
