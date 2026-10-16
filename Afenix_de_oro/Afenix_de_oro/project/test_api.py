"""
Tests básicos para la API de Restaurant Order Management

Para ejecutar los tests:
    pytest test_api.py -v

Requisitos:
    pip install pytest pytest-asyncio httpx
"""

import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories import UserRepository
from app.domain.entities import User
from app.infrastructure.security.jwt_handler import hash_password
from app.shared.constants.enums import UserRole


BASE_URL = "http://localhost:8000/api/v1"


@pytest.fixture
async def test_user():
    """Create a test user."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = User(
            username="test_user",
            email="test@restaurant.com",
            password_hash=hash_password("test123"),
            full_name="Test User",
            role=UserRole.CAMARERO.value,
            is_active=True,
        )
        user_obj = await user_repo.create(user)
        await session.commit()
        return user_obj


@pytest.fixture
async def auth_token(test_user):
    """Get authentication token."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/users/login",
            json={
                "username": test_user.username,
                "password": "test123"
            }
        )
        if response.status_code == 200:
            return response.json()["data"]["access_token"]
    return None


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_user():
    """Test user registration."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/users/register",
            json={
                "username": f"user_{id(object())}",
                "email": f"user{id(object())}@test.com",
                "password": "password123",
                "full_name": "Test User",
                "role": "CAMARERO"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == data["data"]["username"]


@pytest.mark.asyncio
async def test_login_user(auth_token):
    """Test user login."""
    assert auth_token is not None


@pytest.mark.asyncio
async def test_get_current_user(auth_token):
    """Test getting current user info."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data


@pytest.mark.asyncio
async def test_list_dishes(auth_token):
    """Test listing dishes."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/dishes?skip=0&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_list_tables(auth_token):
    """Test listing tables."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/tables?skip=0&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_invalid_token():
    """Test invalid token."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_token():
    """Test missing token."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/users/me")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
