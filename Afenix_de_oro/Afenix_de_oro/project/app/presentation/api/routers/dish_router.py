"""Dish API routers."""
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, status, Query, File, UploadFile, HTTPException

from app.infrastructure.database.repositories import DishRepository, CategoryRepository
from app.application.use_cases.dish_use_cases import (
    CreateDishUseCase, GetDishUseCase, ListDishesUseCase, UpdateDishUseCase,
    DeleteDishUseCase, GetDishesByCategoryUseCase, SearchDishesUseCase,
    GetAvailableDishesUseCase
)
from app.application.dto import DishCreateRequest, DishUpdateRequest, DishResponse, SubcategoryBriefResponse, SubcategoryOptionResponse
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_dish_repository, get_current_user, require_role, get_history_repository, get_category_repository
)
from app.infrastructure.database.repositories import HistoryRepository, CategoryRepository

router = APIRouter(prefix="/api/v1/dishes", tags=["Dishes"])

# Configuración de imágenes de platos
project_root = Path(__file__).resolve().parents[4]
static_dir = project_root / "static"
dishes_upload_dir = static_dir / "uploads" / "dishes"
dishes_upload_dir.mkdir(parents=True, exist_ok=True)
ALLOWED_DISH_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
MAX_DISH_SIZE = 3 * 1024 * 1024

def _dish_image_url(image_path: str | None) -> str | None:
    if not image_path:
        return None
    if image_path.startswith("/"):
        return image_path
    return f"/{image_path.lstrip('/')}"

def _to_dish_response(dish) -> DishResponse:
    image_path = getattr(dish, 'image_path', None)
    subs = []
    for sub in getattr(dish, 'subcategories', []) or []:
        opts = []
        for o in getattr(sub, 'options', []) or []:
            opts.append(SubcategoryOptionResponse(id=o.id, subcategory_id=o.subcategory_id, name=o.name, created_at=o.created_at, updated_at=o.updated_at))
        subs.append(SubcategoryBriefResponse(id=sub.id, name=sub.name, description=sub.description, options=opts))
    return DishResponse(
        id=dish.id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        estimated_time=dish.estimated_time,
        category=dish.category,
        category_id=getattr(dish, 'category_id', None),
        category_name=getattr(dish, 'category_name', None) or dish.category,
        is_available=dish.is_available,
        preparation_notes=dish.preparation_notes,
        image_path=image_path,
        image_url=_dish_image_url(image_path),
        subcategories=subs,
        created_at=dish.created_at,
        updated_at=dish.updated_at,
    )


async def _log_history_safe(history_repo: HistoryRepository, **kwargs):
    try:
        await history_repo.create(**kwargs)
    except Exception:
        pass

@router.post("", response_model=ResponseSchema[DishResponse], status_code=status.HTTP_201_CREATED)
async def create_dish(
    request: DishCreateRequest,
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
):
    """
    Create a new dish (admin only).
    
    - **name**: Dish name
    - **price**: Price in cents (> 0)
    - **estimated_time**: Estimated preparation time in seconds (> 0)
    - **category**: Dish category (deprecated)
    - **category_id**: Category id (preferred)
    - **description**: Optional description
    - **preparation_notes**: Optional preparation notes
    """
    current_user = await require_role("ADMIN")(current_user)
    use_case = CreateDishUseCase(dish_repository, category_repo)
    dish = await use_case.execute(
        name=request.name,
        price=request.price,
        estimated_time=request.estimated_time,
        category=request.category,
        category_id=request.category_id,
        description=request.description,
        preparation_notes=request.preparation_notes,
        is_available=request.is_available,
        created_by=current_user["user_id"],
    )
    await _log_history_safe(
        history_repo,
        category="PLATOS",
        action="CREADO",
        entity_type="PLATO",
        entity_id=dish.id,
        entity_name=dish.name,
        description=f"Plato '{dish.name}' creado (categoría {dish.category}, precio {dish.price/100:.2f}, {'Disponible' if dish.is_available else 'Agotado'})",
        details={"name": dish.name, "category": dish.category, "price": dish.price, "is_available": dish.is_available},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
    
    return ResponseSchema(
        success=True,
        message="Plato creado exitosamente",
        data=_to_dish_response(dish)
    )


@router.post("/{dish_id}/image", response_model=ResponseSchema[DishResponse])
async def upload_dish_image(
    dish_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
):
    """Sube/actualiza la imagen de un plato. Solo ADMIN. Imagen opcional pero si se envía, se guarda."""
    current_user = await require_role("ADMIN")(current_user)
    # Validar plato existe
    dish = await dish_repository.get_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    if file.content_type not in ALLOWED_DISH_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de imagen no permitido. Use PNG, JPEG, WEBP o GIF.")
    content = await file.read()
    if len(content) > MAX_DISH_SIZE:
        raise HTTPException(status_code=400, detail="Imagen demasiado grande. Máximo 3MB.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Archivo vacío.")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        mapping = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
        ext = mapping.get(file.content_type, ".png")
    filename = f"dish_{dish_id}_{uuid.uuid4().hex}{ext}"
    dest = dishes_upload_dir / filename
    with open(dest, "wb") as f:
        f.write(content)
    # Borrar imagen anterior si existe
    old_path = getattr(dish, 'image_path', None)
    if old_path:
        try:
            old_full = static_dir / Path(old_path.replace("/static/", "").lstrip("/"))
            if old_full.exists() and old_full.resolve() != dest.resolve():
                old_full.unlink(missing_ok=True)
        except Exception:
            pass
    # Actualizar plato con nueva ruta
    new_path = f"/static/uploads/dishes/{filename}"
    # Usar use case de actualización
    use_case = UpdateDishUseCase(dish_repository)
    updated = await use_case.execute(dish_id=dish_id, image_path=new_path, updated_by=current_user["user_id"])
    return ResponseSchema(success=True, message="Imagen actualizada correctamente", data=_to_dish_response(updated))


@router.delete("/{dish_id}/image", response_model=ResponseSchema[DishResponse])
async def delete_dish_image(
    dish_id: int,
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
):
    """Elimina la imagen de un plato. Solo ADMIN."""
    current_user = await require_role("ADMIN")(current_user)
    dish = await dish_repository.get_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    old_path = getattr(dish, 'image_path', None)
    if old_path:
        try:
            old_full = static_dir / Path(old_path.replace("/static/", "").lstrip("/"))
            if old_full.exists():
                old_full.unlink(missing_ok=True)
        except Exception:
            pass
    use_case = UpdateDishUseCase(dish_repository)
    updated = await use_case.execute(dish_id=dish_id, image_path="", updated_by=current_user["user_id"])
    # Forzar a None si se pasó cadena vacía (el repo lo tratará como no None, pero queremos limpiar)
    # Si el repo no limpia con cadena vacía, lo hacemos directo
    if updated.image_path == "":
        # Actualizar directo a None
        from sqlalchemy import select
        from app.infrastructure.database.models import DishModel
        result = await dish_repository.session.execute(select(DishModel).where(DishModel.id == dish_id))
        db_dish = result.scalars().first()
        if db_dish:
            db_dish.image_path = None
            await dish_repository.session.commit()
            await dish_repository.session.refresh(db_dish)
            from app.infrastructure.database.repositories.base_repositories import DishRepository as _DR
            # Recargar
            updated = await dish_repository.get_by_id(dish_id)
    return ResponseSchema(success=True, message="Imagen eliminada", data=_to_dish_response(updated))


@router.get("/{dish_id}", response_model=ResponseSchema[DishResponse])
async def get_dish(
    dish_id: int,
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
):
    """Get dish by ID."""
    use_case = GetDishUseCase(dish_repository)
    dish = await use_case.execute(dish_id)
    
    return ResponseSchema(
        success=True,
        message="Plato obtenido exitosamente",
        data=_to_dish_response(dish)
    )


@router.get("", response_model=ResponseSchema[list[DishResponse]])
async def list_dishes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
):
    """List all dishes."""
    use_case = ListDishesUseCase(dish_repository)
    dishes = await use_case.execute(skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Platos obtenidos exitosamente",
        data=[_to_dish_response(d) for d in dishes]
    )


@router.put("/{dish_id}", response_model=ResponseSchema[DishResponse])
async def update_dish(
    dish_id: int,
    request: DishUpdateRequest,
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
):
    """Update dish (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = UpdateDishUseCase(dish_repository, category_repo)
    dish = await use_case.execute(
        dish_id=dish_id,
        name=request.name,
        price=request.price,
        estimated_time=request.estimated_time,
        category=request.category,
        category_id=request.category_id,
        description=request.description,
        is_available=request.is_available,
        preparation_notes=request.preparation_notes,
        updated_by=current_user["user_id"],
    )
    await _log_history_safe(
        history_repo,
        category="PLATOS",
        action="ACTUALIZADO",
        entity_type="PLATO",
        entity_id=dish.id,
        entity_name=dish.name,
        description=f"Plato '{dish.name}' actualizado ({'Disponible' if dish.is_available else 'Agotado'}, categoría {dish.category})",
        details={"updated_fields": request.model_dump(exclude_none=True), "name": dish.name},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
    
    return ResponseSchema(
        success=True,
        message="Plato actualizado exitosamente",
        data=_to_dish_response(dish)
    )


@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish(
    dish_id: int,
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Delete dish (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    dish_before = await dish_repository.get_by_id(dish_id)
    use_case = DeleteDishUseCase(dish_repository)
    await use_case.execute(dish_id)
    if dish_before:
        await _log_history_safe(
            history_repo,
            category="PLATOS",
            action="ELIMINADO",
            entity_type="PLATO",
            entity_id=dish_id,
            entity_name=dish_before.name,
            description=f"Plato '{dish_before.name}' eliminado (categoría {dish_before.category})",
            details={"name": dish_before.name, "category": dish_before.category},
            performed_by=current_user["user_id"],
            performed_by_username=current_user.get("username"),
        )


@router.get("/category/{category}", response_model=ResponseSchema[list[DishResponse]])
async def get_dishes_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
):
    """Get dishes by category."""
    use_case = GetDishesByCategoryUseCase(dish_repository)
    dishes = await use_case.execute(category, skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Platos obtenidos exitosamente",
        data=[_to_dish_response(d) for d in dishes]
    )


@router.get("/search/query", response_model=ResponseSchema[list[DishResponse]])
async def search_dishes(
    query: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
):
    """Search dishes by name or description."""
    use_case = SearchDishesUseCase(dish_repository)
    dishes = await use_case.execute(query, skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Búsqueda completada exitosamente",
        data=[_to_dish_response(d) for d in dishes]
    )


@router.get("/available/list", response_model=ResponseSchema[list[DishResponse]])
async def get_available_dishes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    dish_repository: DishRepository = Depends(get_dish_repository),
):
    """Get available dishes."""
    use_case = GetAvailableDishesUseCase(dish_repository)
    dishes = await use_case.execute(skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Platos disponibles obtenidos exitosamente",
        data=[_to_dish_response(d) for d in dishes]
    )
