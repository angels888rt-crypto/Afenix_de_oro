"""Use cases for dish management."""
from typing import Optional

from app.infrastructure.database.repositories import DishRepository
from app.domain.entities import Dish
from app.shared.exceptions import ValidationException, DuplicateResourceException


class CreateDishUseCase:
    """Use case for creating a dish."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, name: str, price: int, estimated_time: int, category: str, description: Optional[str] = None, preparation_notes: Optional[str] = None, is_available: bool = True, image_path: Optional[str] = None, created_by: Optional[int] = None) -> Dish:
        """Create a new dish."""
        # Validate input
        if price <= 0:
            raise ValidationException("El precio debe ser mayor a 0")
        if estimated_time <= 0:
            raise ValidationException("El tiempo estimado debe ser mayor a 0")
        
        dish = Dish(
            name=name,
            description=description,
            price=price,
            estimated_time=estimated_time,
            category=category,
            is_available=is_available,
            preparation_notes=preparation_notes,
            image_path=image_path,
            created_by=created_by,
        )
        
        return await self.dish_repository.create(dish)


class GetDishUseCase:
    """Use case for getting dish information."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, dish_id: int) -> Dish:
        """Get dish by ID."""
        dish = await self.dish_repository.get_by_id(dish_id)
        if not dish:
            raise ValidationException("Plato no encontrado")
        return dish


class ListDishesUseCase:
    """Use case for listing dishes."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, skip: int = 0, limit: int = 10) -> list[Dish]:
        """List dishes."""
        return await self.dish_repository.list(skip, limit)


class UpdateDishUseCase:
    """Use case for updating dish."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, dish_id: int, name: Optional[str] = None, price: Optional[int] = None, estimated_time: Optional[int] = None, category: Optional[str] = None, description: Optional[str] = None, is_available: Optional[bool] = None, preparation_notes: Optional[str] = None, image_path: Optional[str] = None, updated_by: Optional[int] = None) -> Dish:
        """Update dish."""
        dish = await self.dish_repository.get_by_id(dish_id)
        if not dish:
            raise ValidationException("Plato no encontrado")
        
        if price is not None and price <= 0:
            raise ValidationException("El precio debe ser mayor a 0")
        if estimated_time is not None and estimated_time <= 0:
            raise ValidationException("El tiempo estimado debe ser mayor a 0")
        
        dish.name = name or dish.name
        dish.description = description if description is not None else dish.description
        dish.price = price or dish.price
        dish.estimated_time = estimated_time or dish.estimated_time
        dish.category = category or dish.category
        if is_available is not None:
            dish.is_available = is_available
        dish.preparation_notes = preparation_notes if preparation_notes is not None else dish.preparation_notes
        if image_path is not None:
            dish.image_path = image_path
        dish.updated_by = updated_by
        
        return await self.dish_repository.update(dish_id, dish)


class DeleteDishUseCase:
    """Use case for deleting dish."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, dish_id: int) -> bool:
        """Delete dish."""
        dish = await self.dish_repository.get_by_id(dish_id)
        if not dish:
            raise ValidationException("Plato no encontrado")
        return await self.dish_repository.delete(dish_id)


class GetDishesByCategoryUseCase:
    """Use case for getting dishes by category."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, category: str, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Get dishes by category."""
        return await self.dish_repository.get_by_category(category, skip, limit)


class SearchDishesUseCase:
    """Use case for searching dishes."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, query: str, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Search dishes."""
        if not query or len(query.strip()) < 2:
            raise ValidationException("La búsqueda debe tener al menos 2 caracteres")
        return await self.dish_repository.search(query, skip, limit)


class GetAvailableDishesUseCase:
    """Use case for getting available dishes."""
    
    def __init__(self, dish_repository: DishRepository):
        self.dish_repository = dish_repository
    
    async def execute(self, skip: int = 0, limit: int = 10) -> list[Dish]:
        """Get available dishes."""
        return await self.dish_repository.get_available(skip, limit)
