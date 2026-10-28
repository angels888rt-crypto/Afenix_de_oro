"""Subcategory API routers."""
from fastapi import APIRouter, Depends, status, Query, HTTPException
from app.infrastructure.database.repositories import (
    SubcategoryRepository, SubcategoryOptionRepository,
    DishSubcategoryRepository, DishRepository,
    get_subcategory_repository, get_subcategory_option_repository,
    get_dish_subcategory_repository, get_dish_repository
)
from app.application.use_cases.subcategory_use_cases import (
    CreateSubcategoryUseCase, GetSubcategoryUseCase, ListSubcategoriesUseCase,
    UpdateSubcategoryUseCase, DeleteSubcategoryUseCase,
    CreateSubcategoryOptionUseCase, GetSubcategoryOptionsUseCase,
    UpdateSubcategoryOptionUseCase, DeleteSubcategoryOptionUseCase,
    LinkDishesToSubcategoryUseCase, GetSubcategoriesForDishUseCase,
    GetDishesForSubcategoryUseCase
)
from app.application.dto import (
    SubcategoryCreateRequest, SubcategoryUpdateRequest, SubcategoryResponse,
    SubcategoryOptionCreateRequest, SubcategoryOptionUpdateRequest,
    SubcategoryOptionResponse, DishSubcategoryLinkRequest
)
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_current_user, require_role, get_subcategory_repository,
    get_subcategory_option_repository, get_dish_subcategory_repository,
    get_dish_repository
)
from app.infrastructure.database.repositories import HistoryRepository
from app.presentation.api.dependencies.auth_dependencies import get_history_repository

router = APIRouter(prefix="/api/v1/subcategories", tags=["Subcategories"])


def _to_response(sub) -> SubcategoryResponse:
    return SubcategoryResponse(
        id=sub.id, name=sub.name, description=sub.description,
        is_active=sub.is_active, created_at=sub.created_at, updated_at=sub.updated_at
    )


def _to_option_response(opt) -> SubcategoryOptionResponse:
    return SubcategoryOptionResponse(
        id=opt.id, subcategory_id=opt.subcategory_id, name=opt.name,
        sort_order=opt.sort_order, created_at=opt.created_at, updated_at=opt.updated_at
    )


# ==================== Subcategory CRUD ====================

@router.get("", response_model=ResponseSchema[list[SubcategoryResponse]])
async def list_subcategories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    subcategory_repo: SubcategoryRepository = Depends(get_subcategory_repository),
):
    """List subcategories - available to any authenticated user."""
    use_case = ListSubcategoriesUseCase(subcategory_repo)
    subs = await use_case.execute(skip, limit)
    return ResponseSchema(success=True, message="Subcategorías obtenidas",
                          data=[_to_response(s) for s in subs])


@router.get("/{subcategory_id}", response_model=ResponseSchema[SubcategoryResponse])
async def get_subcategory(
    subcategory_id: int,
    current_user: dict = Depends(get_current_user),
    subcategory_repo: SubcategoryRepository = Depends(get_subcategory_repository),
):
    """Get subcategory by ID."""
    use_case = GetSubcategoryUseCase(subcategory_repo)
    sub = await use_case.execute(subcategory_id)
    return ResponseSchema(success=True, message="Subcategoría obtenida",
                          data=_to_response(sub))


@router.post("", response_model=ResponseSchema[SubcategoryResponse],
             status_code=status.HTTP_201_CREATED)
async def create_subcategory(
    request: SubcategoryCreateRequest,
    current_user: dict = Depends(get_current_user),
    subcategory_repo: SubcategoryRepository = Depends(get_subcategory_repository),
    dish_repo: DishRepository = Depends(get_dish_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Create a new subcategory (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = CreateSubcategoryUseCase(subcategory_repo, dish_repo)
    sub = await use_case.execute(
        name=request.name, description=request.description,
        dish_ids=request.dish_ids, created_by=current_user["user_id"]
    )
    await _log_history(history_repo, "SUBCATEGORÍAS", "CREADO", "SUBCATEGORÍA",
                       sub.id, sub.name, f"Subcategoría '{sub.name}' creada",
                       current_user["user_id"], current_user.get("username"))
    return ResponseSchema(success=True, message="Subcategoría creada",
                          data=_to_response(sub))


@router.put("/{subcategory_id}", response_model=ResponseSchema[SubcategoryResponse])
async def update_subcategory(
    subcategory_id: int,
    request: SubcategoryUpdateRequest,
    current_user: dict = Depends(get_current_user),
    subcategory_repo: SubcategoryRepository = Depends(get_subcategory_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Update subcategory (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = UpdateSubcategoryUseCase(subcategory_repo)
    sub = await use_case.execute(
        subcategory_id=subcategory_id, name=request.name,
        description=request.description, is_active=request.is_active,
        updated_by=current_user["user_id"]
    )
    await _log_history(history_repo, "SUBCATEGORÍAS", "ACTUALIZADO", "SUBCATEGORÍA",
                       sub.id, sub.name, f"Subcategoría '{sub.name}' actualizada",
                       current_user["user_id"], current_user.get("username"))
    return ResponseSchema(success=True, message="Subcategoría actualizada",
                          data=_to_response(sub))


@router.delete("/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcategory(
    subcategory_id: int,
    current_user: dict = Depends(get_current_user),
    subcategory_repo: SubcategoryRepository = Depends(get_subcategory_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Delete subcategory (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = DeleteSubcategoryUseCase(subcategory_repo)
    await use_case.execute(subcategory_id)
    await _log_history(history_repo, "SUBCATEGORÍAS", "ELIMINADO", "SUBCATEGORÍA",
                       subcategory_id, None, f"Subcategoría ID {subcategory_id} eliminada",
                       current_user["user_id"], current_user.get("username"))


# ==================== Subcategory Options ====================

@router.get("/{subcategory_id}/options", response_model=ResponseSchema[list[SubcategoryOptionResponse]])
async def get_subcategory_options(
    subcategory_id: int,
    current_user: dict = Depends(get_current_user),
    option_repo: SubcategoryOptionRepository = Depends(get_subcategory_option_repository),
):
    """Get options for a subcategory."""
    use_case = GetSubcategoryOptionsUseCase(option_repo)
    opts = await use_case.execute(subcategory_id)
    return ResponseSchema(success=True, message="Opciones obtenidas",
                          data=[_to_option_response(o) for o in opts])


@router.post("/{subcategory_id}/options", response_model=ResponseSchema[SubcategoryOptionResponse],
             status_code=status.HTTP_201_CREATED)
async def create_subcategory_option(
    subcategory_id: int,
    request: SubcategoryOptionCreateRequest,
    current_user: dict = Depends(get_current_user),
    option_repo: SubcategoryOptionRepository = Depends(get_subcategory_option_repository),
    subcategory_repo: SubcategoryRepository = Depends(get_subcategory_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Create a new option for a subcategory (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = CreateSubcategoryOptionUseCase(option_repo, subcategory_repo)
    opt = await use_case.execute(
        subcategory_id=subcategory_id, name=request.name,
        sort_order=request.sort_order, created_by=current_user["user_id"]
    )
    await _log_history(history_repo, "SUBCATEGORÍAS", "CREADO", "OPCIÓN_SUBCATEGORÍA",
                       opt.id, opt.name, f"Opción '{opt.name}' creada para subcategoría {subcategory_id}",
                       current_user["user_id"], current_user.get("username"))
    return ResponseSchema(success=True, message="Opción creada",
                          data=_to_option_response(opt))


@router.put("/options/{option_id}", response_model=ResponseSchema[SubcategoryOptionResponse])
async def update_subcategory_option(
    option_id: int,
    request: SubcategoryOptionUpdateRequest,
    current_user: dict = Depends(get_current_user),
    option_repo: SubcategoryOptionRepository = Depends(get_subcategory_option_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Update subcategory option (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = UpdateSubcategoryOptionUseCase(option_repo)
    opt = await use_case.execute(
        option_id=option_id, name=request.name,
        sort_order=request.sort_order, updated_by=current_user["user_id"]
    )
    await _log_history(history_repo, "SUBCATEGORÍAS", "ACTUALIZADO", "OPCIÓN_SUBCATEGORÍA",
                       opt.id, opt.name, f"Opción '{opt.name}' actualizada",
                       current_user["user_id"], current_user.get("username"))
    return ResponseSchema(success=True, message="Opción actualizada",
                          data=_to_option_response(opt))


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcategory_option(
    option_id: int,
    current_user: dict = Depends(get_current_user),
    option_repo: SubcategoryOptionRepository = Depends(get_subcategory_option_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Delete subcategory option (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = DeleteSubcategoryOptionUseCase(option_repo)
    await use_case.execute(option_id)
    await _log_history(history_repo, "SUBCATEGORÍAS", "ELIMINADO", "OPCIÓN_SUBCATEGORÍA",
                       option_id, None, f"Opción ID {option_id} eliminada",
                       current_user["user_id"], current_user.get("username"))


# ==================== Dish-Subcategory Links ====================

@router.get("/{subcategory_id}/dishes", response_model=ResponseSchema[list[int]])
async def get_dishes_for_subcategory(
    subcategory_id: int,
    current_user: dict = Depends(get_current_user),
    dish_sub_repo: DishSubcategoryRepository = Depends(get_dish_subcategory_repository),
):
    """Get dish IDs linked to a subcategory."""
    use_case = GetDishesForSubcategoryUseCase(dish_sub_repo)
    dish_ids = await use_case.execute(subcategory_id)
    return ResponseSchema(success=True, message="Platos obtenidos", data=dish_ids)


@router.post("/{subcategory_id}/dishes", response_model=ResponseSchema[list[int]])
async def link_dishes_to_subcategory(
    subcategory_id: int,
    request: DishSubcategoryLinkRequest,
    current_user: dict = Depends(get_current_user),
    dish_sub_repo: DishSubcategoryRepository = Depends(get_dish_subcategory_repository),
    dish_repo: DishRepository = Depends(get_dish_repository),
    subcategory_repo: SubcategoryRepository = Depends(get_subcategory_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Link dishes to a subcategory (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = LinkDishesToSubcategoryUseCase(dish_sub_repo, dish_repo, subcategory_repo)
    linked = await use_case.execute(subcategory_id, request.dish_ids)
    await _log_history(history_repo, "SUBCATEGORÍAS", "ACTUALIZADO", "SUBCATEGORÍA",
                       subcategory_id, None,
                       f"{len(linked)} platos vinculados a subcategoría {subcategory_id}",
                       current_user["user_id"], current_user.get("username"))
    return ResponseSchema(success=True, message="Platos vinculados", data=linked)


async def _log_history(history_repo, category, action, entity_type,
                       entity_id, entity_name, description,
                       performed_by, performed_by_username):
    try:
        await history_repo.create(
            category=category, action=action, entity_type=entity_type,
            entity_id=entity_id, entity_name=entity_name,
            description=description, performed_by=performed_by,
            performed_by_username=performed_by_username
        )
    except Exception:
        pass
