import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.application.use_cases.subcategory_use_cases import DeleteSubcategoryUseCase
from app.infrastructure.database.repositories.base_repositories import (
    SubcategoryRepository,
)


class ScalarResult:
    def scalar(self):
        return 0


class FakeSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return ScalarResult()


def test_subcategory_dish_count_excludes_soft_deleted_dishes() -> None:
    session = FakeSession()
    repository = SubcategoryRepository(session)

    count = asyncio.run(repository.count_dishes(4))

    sql = str(session.statement.compile(compile_kwargs={"literal_binds": True}))
    assert count == 0
    assert "JOIN dishes" in sql
    assert "dishes.deleted_at IS NULL" in sql


def test_delete_subcategory_allowed_when_only_deleted_dishes_were_linked() -> None:
    subcategory = SimpleNamespace(id=4, name="Color del arroz")
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=subcategory),
        count_dishes=AsyncMock(return_value=0),
        delete=AsyncMock(return_value=True),
    )

    deleted = asyncio.run(DeleteSubcategoryUseCase(repository).execute(4))

    assert deleted is True
    repository.count_dishes.assert_awaited_once_with(4)
    repository.delete.assert_awaited_once_with(4)


def test_deleted_dish_links_are_removed_when_dish_is_soft_deleted() -> None:
    from app.infrastructure.database.repositories.base_repositories import DishRepository

    dish = SimpleNamespace(
        id=9,
        deleted_at=None,
        is_available=True,
        updated_at=None,
    )
    link = SimpleNamespace(dish_id=9, subcategory_id=4)

    class DishDeleteSession:
        def __init__(self):
            self.execute_calls = 0
            self.deleted_links = []
            self.committed = False

        async def execute(self, _statement):
            self.execute_calls += 1
            if self.execute_calls == 1:
                return SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: dish))
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [link]))

        async def delete(self, value):
            self.deleted_links.append(value)

        async def commit(self):
            self.committed = True

    session = DishDeleteSession()
    deleted = asyncio.run(DishRepository(session).delete(9))

    assert deleted is True
    assert session.deleted_links == [link]
    assert session.committed is True
    assert dish.deleted_at is not None
    assert dish.deleted_at.tzinfo == timezone.utc
