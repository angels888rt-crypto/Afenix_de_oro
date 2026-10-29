import asyncio
from datetime import datetime, timezone

from httpx import ASGITransport, AsyncClient

from app.domain.entities import Subcategory
from app.presentation.api.dependencies.auth_dependencies import (
    get_current_user,
    get_subcategory_repository,
)
from main import app


def test_subcategory_collection_route_is_registered() -> None:
    route = next(
        route
        for route in app.routes
        if route.path == "/api/v1/subcategories" and "GET" in route.methods
    )

    assert route.name == "list_subcategories"


def test_list_subcategories_returns_successful_response() -> None:
    class FakeSubcategoryRepository:
        async def list(self, skip: int, limit: int) -> list[Subcategory]:
            return [
                Subcategory(
                    id=1,
                    name="Tamaño",
                    description=None,
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            ]

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 1,
        "username": "test",
        "role": "ADMIN",
    }
    app.dependency_overrides[get_subcategory_repository] = FakeSubcategoryRepository

    async def request_subcategories():
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            return await client.get("/api/v1/subcategories?limit=100")

    try:
        response = asyncio.run(request_subcategories())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"][0]["name"] == "Tamaño"
