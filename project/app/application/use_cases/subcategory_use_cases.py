"""Use cases for subcategory management."""
from typing import Optional
from app.infrastructure.database.repositories import (
    SubcategoryRepository, SubcategoryOptionRepository,
    DishSubcategoryRepository, DishRepository, OrderRepository
)
from app.domain.entities import Subcategory, SubcategoryOption
from app.shared.exceptions import ValidationException, DuplicateResourceException
from fastapi import HTTPException, status


class CreateSubcategoryUseCase:
    """Use case for creating a subcategory."""

    def __init__(self, subcategory_repository: SubcategoryRepository, dish_repository: DishRepository):
        self.subcategory_repository = subcategory_repository
        self.dish_repository = dish_repository

    async def execute(self, name: str, description: Optional[str] = None,
                      dish_ids: Optional[list[int]] = None, created_by: Optional[int] = None) -> Subcategory:
        name = name.strip() if name else ""
        if not name or len(name) < 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="El nombre de la subcategoría debe tener al menos 2 caracteres")
        if len(name) > 80:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="El nombre no puede superar 80 caracteres")

        existing = await self.subcategory_repository.get_by_name(name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"La subcategoría '{name}' ya existe")

        subcat = Subcategory(
            name=name, description=description,
            is_active=True, created_by=created_by
        )
        created = await self.subcategory_repository.create(subcat)

        # Link dishes if provided
        if dish_ids:
            dish_sub_repo = DishSubcategoryRepository(self.subcategory_repository.session)
            for dish_id in dish_ids:
                # Verify dish exists
                dish = await self.dish_repository.get_by_id(dish_id)
                if dish:
                    await dish_sub_repo.link_dish_to_subcategory(dish_id, created.id)

        return created


class GetSubcategoryUseCase:
    """Use case for getting a subcategory."""

    def __init__(self, subcategory_repository: SubcategoryRepository):
        self.subcategory_repository = subcategory_repository

    async def execute(self, subcategory_id: int) -> Subcategory:
        subcat = await self.subcategory_repository.get_by_id(subcategory_id)
        if not subcat:
            raise ValidationException("Subcategoría no encontrada")
        return subcat


class ListSubcategoriesUseCase:
    """Use case for listing subcategories."""

    def __init__(self, subcategory_repository: SubcategoryRepository):
        self.subcategory_repository = subcategory_repository

    async def execute(self, skip: int = 0, limit: int = 100) -> list[Subcategory]:
        return await self.subcategory_repository.list(skip, limit)


class UpdateSubcategoryUseCase:
    """Use case for updating a subcategory."""

    def __init__(self, subcategory_repository: SubcategoryRepository):
        self.subcategory_repository = subcategory_repository

    async def execute(self, subcategory_id: int, name: Optional[str] = None,
                      description: Optional[str] = None,
                      is_active: Optional[bool] = None,
                      updated_by: Optional[int] = None) -> Subcategory:
        subcat = await self.subcategory_repository.get_by_id(subcategory_id)
        if not subcat:
            raise ValidationException("Subcategoría no encontrada")

        if name is not None:
            name = name.strip()
            if len(name) < 2:
                raise ValidationException("El nombre debe tener al menos 2 caracteres")
            existing = await self.subcategory_repository.get_by_name(name)
            if existing and existing.id != subcategory_id:
                raise ValidationException(f"La subcategoría '{name}' ya existe")

        updated_entity = Subcategory(
            name=name if name is not None else None,
            description=description,
            is_active=is_active,
            updated_by=updated_by
        )
        updated = await self.subcategory_repository.update(subcategory_id, updated_entity)
        if not updated:
            raise ValidationException("No se pudo actualizar la subcategoría")
        return updated


class DeleteSubcategoryUseCase:
    """Use case for deleting a subcategory."""

    def __init__(self, subcategory_repository: SubcategoryRepository):
        self.subcategory_repository = subcategory_repository

    async def execute(self, subcategory_id: int) -> bool:
        subcat = await self.subcategory_repository.get_by_id(subcategory_id)
        if not subcat:
            raise ValidationException("Subcategoría no encontrada")
        count = await self.subcategory_repository.count_dishes(subcat.name)
        if count > 0:
            raise ValidationException(
                f"No se puede eliminar la subcategoría '{subcat.name}' porque tiene {count} plato(s) asociado(s)."
            )
        return await self.subcategory_repository.delete(subcategory_id)


class CreateSubcategoryOptionUseCase:
    """Use case for creating a subcategory option."""

    def __init__(self, option_repository: SubcategoryOptionRepository,
                 subcategory_repository: SubcategoryRepository):
        self.option_repository = option_repository
        self.subcategory_repository = subcategory_repository

    async def execute(self, subcategory_id: int, name: str,
                      sort_order: int = 0, created_by: Optional[int] = None) -> SubcategoryOption:
        # Verify subcategory exists
        subcat = await self.subcategory_repository.get_by_id(subcategory_id)
        if not subcat:
            raise ValidationException("Subcategoría no encontrada")

        name = name.strip() if name else ""
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="El nombre de la opción no puede estar vacío")

        # Check duplicate within subcategory
        existing_opts = await self.option_repository.get_by_subcategory(subcategory_id)
        if any(o.name.lower() == name.lower() for o in existing_opts):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"La opción '{name}' ya existe en esta subcategoría")

        opt = SubcategoryOption(
            subcategory_id=subcategory_id, name=name,
            sort_order=sort_order, created_by=created_by
        )
        return await self.option_repository.create(opt)


class GetSubcategoryOptionsUseCase:
    """Use case for getting options of a subcategory."""

    def __init__(self, option_repository: SubcategoryOptionRepository):
        self.option_repository = option_repository

    async def execute(self, subcategory_id: int) -> list[SubcategoryOption]:
        return await self.option_repository.get_by_subcategory(subcategory_id)


class UpdateSubcategoryOptionUseCase:
    """Use case for updating a subcategory option."""

    def __init__(self, option_repository: SubcategoryOptionRepository):
        self.option_repository = option_repository

    async def execute(self, option_id: int, name: Optional[str] = None,
                      sort_order: Optional[int] = None,
                      updated_by: Optional[int] = None) -> SubcategoryOption:
        opt = await self.option_repository.get_by_id(option_id)
        if not opt:
            raise ValidationException("Opción no encontrada")

        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationException("El nombre de la opción no puede estar vacío")
            # Check duplicate
            existing_opts = await self.option_repository.get_by_subcategory(opt.subcategory_id)
            if any(o.name.lower() == name.lower() and o.id != option_id for o in existing_opts):
                raise ValidationException(f"La opción '{name}' ya existe en esta subcategoría")

        updated_entity = SubcategoryOption(
            subcategory_id=opt.subcategory_id,
            name=name if name is not None else None,
            sort_order=sort_order if sort_order is not None else 0,
            updated_by=updated_by
        )
        updated = await self.option_repository.update(option_id, updated_entity)
        if not updated:
            raise ValidationException("No se pudo actualizar la opción")
        return updated


class DeleteSubcategoryOptionUseCase:
    """Use case for deleting a subcategory option."""

    def __init__(self, option_repository: SubcategoryOptionRepository):
        self.option_repository = option_repository

    async def execute(self, option_id: int) -> bool:
        return await self.option_repository.delete(option_id)


class LinkDishesToSubcategoryUseCase:
    """Use case for linking dishes to a subcategory."""

    def __init__(self, dish_sub_repository: DishSubcategoryRepository,
                 dish_repository: DishRepository,
                 subcategory_repository: SubcategoryRepository):
        self.dish_sub_repository = dish_sub_repository
        self.dish_repository = dish_repository
        self.subcategory_repository = subcategory_repository

    async def execute(self, subcategory_id: int, dish_ids: list[int]) -> list[int]:
        """Link dishes to subcategory. Returns list of linked dish IDs."""
        # Verify subcategory exists
        subcat = await self.subcategory_repository.get_by_id(subcategory_id)
        if not subcat:
            raise ValidationException("Subcategoría no encontrada")

        linked = []
        for dish_id in dish_ids:
            dish = await self.dish_repository.get_by_id(dish_id)
            if dish:
                await self.dish_sub_repository.link_dish_to_subcategory(dish_id, subcategory_id)
                linked.append(dish_id)
        return linked


class GetSubcategoriesForDishUseCase:
    """Use case for getting subcategories for a dish."""

    def __init__(self, dish_sub_repository: DishSubcategoryRepository):
        self.dish_sub_repository = dish_sub_repository

    async def execute(self, dish_id: int) -> list[Subcategory]:
        return await self.dish_sub_repository.get_subcategories_for_dish(dish_id)


class GetDishesForSubcategoryUseCase:
    """Use case for getting dishes for a subcategory."""

    def __init__(self, dish_sub_repository: DishSubcategoryRepository):
        self.dish_sub_repository = dish_sub_repository

    async def execute(self, subcategory_id: int) -> list[int]:
        return await self.dish_sub_repository.get_dishes_for_subcategory(subcategory_id)
