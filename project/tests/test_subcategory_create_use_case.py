import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.application.use_cases.subcategory_use_cases import CreateSubcategoryUseCase


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
