"""Repository interfaces."""
from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Base repository interface."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def update(self, id: int, entity: T) -> Optional[T]:
        """Update entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Delete entity (soft delete)."""
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 10) -> list[T]:
        """List entities with pagination."""
        pass


class IUserRepository(IRepository[T], ABC):
    """User repository interface."""
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[T]:
        """Get user by username."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[T]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def get_by_role(self, role: str, skip: int = 0, limit: int = 10) -> list[T]:
        """Get users by role."""
        pass


class ITableRepository(IRepository[T], ABC):
    """Table repository interface."""
    
    @abstractmethod
    async def get_by_number(self, table_number: int) -> Optional[T]:
        """Get table by number."""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 10) -> list[T]:
        """Get tables by status."""
        pass


class IDishRepository(IRepository[T], ABC):
    """Dish repository interface."""
    
    @abstractmethod
    async def get_by_category(self, category: str, skip: int = 0, limit: int = 10) -> list[T]:
        """Get dishes by category."""
        pass
    
    @abstractmethod
    async def search(self, query: str, skip: int = 0, limit: int = 10) -> list[T]:
        """Search dishes by name or description."""
        pass
    
    @abstractmethod
    async def get_available(self, skip: int = 0, limit: int = 10) -> list[T]:
        """Get available dishes."""
        pass


class IOrderRepository(IRepository[T], ABC):
    """Order repository interface."""
    
    @abstractmethod
    async def get_by_table_id(self, table_id: int) -> Optional[T]:
        """Get active order for table."""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 10) -> list[T]:
        """Get orders by status."""
        pass
    
    @abstractmethod
    async def get_by_camarero_id(self, camarero_id: int, skip: int = 0, limit: int = 10) -> list[T]:
        """Get orders by camarero."""
        pass


class IOrderItemRepository(IRepository[T], ABC):
    """Order item repository interface."""
    
    @abstractmethod
    async def get_by_order_id(self, order_id: int) -> list[T]:
        """Get items for order."""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 10) -> list[T]:
        """Get order items by status."""
        pass


class INotificationRepository(IRepository[T], ABC):
    """Notification repository interface."""
    
    @abstractmethod
    async def get_by_order_id(self, order_id: int) -> list[T]:
        """Get notifications for order."""
        pass
    
    @abstractmethod
    async def get_unread_by_role(self, role: str, skip: int = 0, limit: int = 10) -> list[T]:
        """Get unread notifications for role."""
        pass
    
    @abstractmethod
    async def mark_as_read(self, notification_id: int) -> Optional[T]:
        """Mark notification as read."""
        pass
