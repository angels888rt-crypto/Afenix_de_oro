"""Use cases for subcategories."""
from typing import Optional
from app.infrastructure.database.repositories import SubcategoryRepository
from app.domain.entities import Subcategory, SubcategoryOption
from app.shared.exceptions import ValidationException


class CreateSubcategoryUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo = sub_repo
    async def execute(self, name: str, description: Optional[str]=None, dish_ids: Optional[list[int]]=None, options: Optional[list[str]]=None, created_by: Optional[int]=None) -> Subcategory:
        name = name.strip()
        if len(name)<2:
            raise ValidationException("El nombre de la subcategoría debe tener al menos 2 caracteres")
        if len(name)>80:
            raise ValidationException("Nombre muy largo")
        existing = await self.sub_repo.get_by_name(name)
        if existing:
            raise ValidationException(f"La subcategoría '{name}' ya existe")
        dish_ids = dish_ids or []
        options = [o.strip() for o in (options or []) if o and o.strip()]
        # validate unique options
        if len(options)!=len(set([o.lower() for o in options])):
            raise ValidationException("Las opciones deben ser únicas dentro de la subcategoría")
        sub = Subcategory(name=name, description=description, dish_ids=dish_ids, options=[SubcategoryOption(name=o) for o in options], created_by=created_by)
        return await self.sub_repo.create(sub)

class ListSubcategoriesUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, skip=0, limit=100) -> list[Subcategory]:
        return await self.sub_repo.list(skip, limit)

class GetSubcategoryUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, sub_id:int) -> Subcategory:
        sub = await self.sub_repo.get_by_id(sub_id)
        if not sub:
            raise ValidationException("Subcategoría no encontrada")
        return sub

class UpdateSubcategoryUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, sub_id:int, name:Optional[str]=None, description:Optional[str]=None, dish_ids:Optional[list[int]]=None, updated_by:Optional[int]=None) -> Subcategory:
        sub = await self.sub_repo.get_by_id(sub_id)
        if not sub:
            raise ValidationException("Subcategoría no encontrada")
        if name is not None:
            name=name.strip()
            if len(name)<2:
                raise ValidationException("Nombre debe tener al menos 2 caracteres")
            exist = await self.sub_repo.get_by_name(name)
            if exist and exist.id!=sub_id:
                raise ValidationException(f"La subcategoría '{name}' ya existe")
        update = Subcategory(name=name if name is not None else None, description=description, dish_ids=dish_ids, updated_by=updated_by)
        # keep original name if not updating for repo logic
        updated = await self.sub_repo.update(sub_id, update)
        if not updated:
            raise ValidationException("No se pudo actualizar")
        return updated

class DeleteSubcategoryUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, sub_id:int) -> bool:
        sub = await self.sub_repo.get_by_id(sub_id)
        if not sub:
            raise ValidationException("Subcategoría no encontrada")
        ok = await self.sub_repo.delete(sub_id)
        if not ok:
            raise ValidationException("No se pudo eliminar")
        return True

class CreateOptionUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, sub_id:int, name:str, created_by:Optional[int]=None) -> SubcategoryOption:
        name=name.strip()
        if not name or len(name)<1 or len(name)>80:
            raise ValidationException("Nombre de opción inválido")
        opt = await self.sub_repo.create_option(sub_id, name, created_by)
        if not opt:
            raise ValidationException("No se pudo crear la opción (duplicada o subcategoría no existe)")
        return opt

class UpdateOptionUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, sub_id:int, option_id:int, name:str, updated_by:Optional[int]=None) -> SubcategoryOption:
        name=name.strip()
        if not name or len(name)>80:
            raise ValidationException("Nombre inválido")
        opt = await self.sub_repo.update_option(sub_id, option_id, name, updated_by)
        if not opt:
            raise ValidationException("No se pudo actualizar (duplicada o no existe)")
        return opt

class DeleteOptionUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, sub_id:int, option_id:int) -> bool:
        # check existence
        ok = await self.sub_repo.delete_option(sub_id, option_id)
        if not ok:
            raise ValidationException("No se pudo eliminar la opción (posiblemente en uso o no existe)")
        return True

class ListOptionsUseCase:
    def __init__(self, sub_repo: SubcategoryRepository):
        self.sub_repo=sub_repo
    async def execute(self, sub_id:int) -> list[SubcategoryOption]:
        sub = await self.sub_repo.get_by_id(sub_id)
        if not sub:
            raise ValidationException("Subcategoría no encontrada")
        return await self.sub_repo.list_options(sub_id)
