"""Dependency injection for API endpoints."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from typing import Optional

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

from app.infrastructure.database.session import get_session
from app.infrastructure.database.repositories import (
    UserRepository, TableRepository, DishRepository, OrderRepository,
    OrderItemRepository, NotificationRepository, CategoryRepository
)
from app.infrastructure.security.jwt_handler import decode_token

security_scheme = HTTPBearer()

def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """Get user repository."""
    return UserRepository(session)


def get_table_repository(session: AsyncSession = Depends(get_session)) -> TableRepository:
    """Get table repository."""
    return TableRepository(session)


def get_dish_repository(session: AsyncSession = Depends(get_session)) -> DishRepository:
    """Get dish repository."""
    return DishRepository(session)


def get_order_repository(session: AsyncSession = Depends(get_session)) -> OrderRepository:
    """Get order repository."""
    return OrderRepository(session)


def get_order_item_repository(session: AsyncSession = Depends(get_session)) -> OrderItemRepository:
    """Get order item repository."""
    return OrderItemRepository(session)


def get_notification_repository(session: AsyncSession = Depends(get_session)) -> NotificationRepository:
    """Get notification repository."""
    return NotificationRepository(session)

def get_category_repository(session: AsyncSession = Depends(get_session)) -> CategoryRepository:
    """Get category repository."""
    return CategoryRepository(session)



def get_history_repository(session: AsyncSession = Depends(get_session)):
    """Get history repository."""
    from app.infrastructure.database.repositories import HistoryRepository
    return HistoryRepository(session)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Get current authenticated user from token."""
    # 🕵️‍♂️ ESPÍA TEMPORAL
    print("--- DETECTANDO CREDENCIALES ---")
    print("Objeto credentials:", credentials)
    print("Token extraído:", credentials.credentials if credentials else "Ninguno")
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"user_id": int(user_id), "username": username, "role": role}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*allowed_roles):
    """Require specific role."""
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para acceder a este recurso",
            )
        return current_user
    
    return role_checker

