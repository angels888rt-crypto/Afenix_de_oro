"""Use cases for category management."""
from typing import Optional
from app.infrastructure.database.repositories import CategoryRepository
from app.domain.entities import Category
from app.shared.exceptions import ValidationException
from typing import Optional
from fastapi import HTTPException, status


class CreateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    async def execute(self, name: str, description: Optional[str] = None, created_by: Optional[int] = None) -> Category:
        # 1. Limpiar espacios en blanco al inicio y al final
        name = name.strip() if name else ""

        # 2. Validaciones de longitud
        if not name or len(name) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de la categoría debe tener al menos 2 caracteres"
            )
        if len(name) > 80:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre no puede superar 80 caracteres"
            )

        # 3. Comprobar si ya existe la categoría
        existing = await self.category_repository.get_by_name(name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La categoría '{name}' ya existe"
            )

        # 4. Crear e insertar si todo está correcto
        cat = Category(name=name, description=description, created_by=created_by)
        return await self.category_repository.create(cat)


class GetCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    async def execute(self, category_id: int) -> Category:
        cat = await self.category_repository.get_by_id(category_id)
        if not cat:
            raise ValidationException("Categoría no encontrada")
        return cat


class ListCategoriesUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    async def execute(self, skip: int = 0, limit: int = 100) -> list[Category]:
        return await self.category_repository.list(skip, limit)


class UpdateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    async def execute(self, category_id: int, name: Optional[str] = None, description: Optional[str] = None, updated_by: Optional[int] = None) -> Category:
        cat = await self.category_repository.get_by_id(category_id)
        if not cat:
            raise ValidationException("Categoría no encontrada")
        if name is not None:
            name = name.strip()
            if len(name) < 2:
                raise ValidationException("El nombre debe tener al menos 2 caracteres")
            # check duplicate ignoring self, case-insensitive
            existing = await self.category_repository.get_by_name(name)
            if existing and existing.id != category_id:
                raise ValidationException(f"La categoría '{name}' ya existe")
        update_entity = Category(name=name if name is not None else None, description=description, updated_by=updated_by)
        # we need to allow description None to be ignored? repo handles None as no change
        # but if description is explicitly None we want to keep? For update, pass as is
        # Hack: temporarily set
        updated = await self.category_repository.update(category_id, update_entity)
        if not updated:
            raise ValidationException("No se pudo actualizar la categoría")
        # if name provided, update_entity already set name; fix sync
        return updated


class DeleteCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    async def execute(self, category_id: int) -> bool:
        cat = await self.category_repository.get_by_id(category_id)
        if not cat:
            raise ValidationException("Categoría no encontrada")
        count = await self.category_repository.count_dishes(cat.name)
        if count > 0:
            raise ValidationException(f"No se puede eliminar la categoría '{cat.name}' porque tiene {count} plato(s) asociado(s). Reasigne o elimine los platos primero.")
        success = await self.category_repository.delete(category_id)
        if not success:
            raise ValidationException("No se pudo eliminar la categoría")
        return True
