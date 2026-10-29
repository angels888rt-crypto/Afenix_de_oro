import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.application.use_cases.subcategory_use_cases import (
    CreateSubcategoryUseCase,
    SetDishesForSubcategoryUseCase,
)


def test_create_subcategory_restores_matching_soft_deleted_record() -> None:
    deleted_subcategory = SimpleNamespace(
        id=7,
        deleted_at=datetime.now(timezone.utc),
    )
    repository = SimpleNamespace(
        get_by_name=AsyncMock(return_value=deleted_subcategory),
        restore=AsyncMock(return_value=SimpleNamespace(id=7, name="Color del arroz")),
        create=AsyncMock(),
        session=SimpleNamespace(),
    )
    dish_repository = SimpleNamespace()

    created = asyncio.run(
        CreateSubcategoryUseCase(repository, dish_repository).execute(
            " Color del arroz "
        )
    )

    assert created.id == 7
    repository.get_by_name.assert_awaited_once_with(
        "Color del arroz", include_deleted=True
    )
    repository.restore.assert_awaited_once()
    repository.create.assert_not_awaited()


def test_create_subcategory_rejects_existing_active_name() -> None:
    active_subcategory = SimpleNamespace(id=7, deleted_at=None)
    repository = SimpleNamespace(
        get_by_name=AsyncMock(return_value=active_subcategory),
        restore=AsyncMock(),
        create=AsyncMock(),
        session=SimpleNamespace(),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            CreateSubcategoryUseCase(repository, SimpleNamespace()).execute(
                "Color del arroz"
            )
        )

    assert exc_info.value.status_code == 409
    assert "ya existe" in exc_info.value.detail
    repository.create.assert_not_awaited()


def test_set_dishes_replaces_existing_subcategory_links() -> None:
    dish_links = SimpleNamespace(
        get_dishes_for_subcategory=AsyncMock(return_value=[1]),
        unlink_dish_from_subcategory=AsyncMock(return_value=True),
        link_dish_to_subcategory=AsyncMock(),
    )
    dish_repository = SimpleNamespace(
        get_by_id=AsyncMock(side_effect=lambda dish_id: SimpleNamespace(id=dish_id))
    )
    subcategory_repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=SimpleNamespace(id=4))
    )

    result = asyncio.run(
        SetDishesForSubcategoryUseCase(
            dish_links, dish_repository, subcategory_repository
        ).execute(4, [2])
    )

    assert result == [2]
    dish_links.unlink_dish_from_subcategory.assert_awaited_once_with(1, 4)
    dish_links.link_dish_to_subcategory.assert_awaited_once_with(2, 4)
