"""Category API routers."""
from fastapi import APIRouter, Depends, status, Query
from app.infrastructure.database.repositories import CategoryRepository
from app.application.use_cases.category_use_cases import (
    CreateCategoryUseCase, GetCategoryUseCase, ListCategoriesUseCase, UpdateCategoryUseCase, DeleteCategoryUseCase
)
from app.application.dto import CategoryCreateRequest, CategoryUpdateRequest, CategoryResponse
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_category_repository, get_current_user, require_role
)

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


def _to_response(cat) -> CategoryResponse:
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        created_at=cat.created_at,
        updated_at=cat.updated_at,
    )


@router.get("", response_model=ResponseSchema[list[CategoryResponse]])
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repository),
):
    """List categories - available to any authenticated user (mesero needs it)."""
    use_case = ListCategoriesUseCase(category_repo)
    cats = await use_case.execute(skip, limit)
    return ResponseSchema(success=True, message="Categorías obtenidas", data=[_to_response(c) for c in cats])


@router.get("/{category_id}", response_model=ResponseSchema[CategoryResponse])
async def get_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repository),
):
    use_case = GetCategoryUseCase(category_repo)
    cat = await use_case.execute(category_id)
    return ResponseSchema(success=True, message="Categoría obtenida", data=_to_response(cat))


@router.post("", response_model=ResponseSchema[CategoryResponse], status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CategoryCreateRequest,
    current_user: dict = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repository),
):
    current_user = await require_role("ADMIN")(current_user)
    use_case = CreateCategoryUseCase(category_repo)
    cat = await use_case.execute(name=request.name, description=request.description, created_by=current_user["user_id"])
    return ResponseSchema(success=True, message="Categoría creada", data=_to_response(cat))


@router.put("/{category_id}", response_model=ResponseSchema[CategoryResponse])
async def update_category(
    category_id: int,
    request: CategoryUpdateRequest,
    current_user: dict = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repository),
):
    current_user = await require_role("ADMIN")(current_user)
    use_case = UpdateCategoryUseCase(category_repo)
    cat = await use_case.execute(category_id=category_id, name=request.name, description=request.description, updated_by=current_user["user_id"])
    return ResponseSchema(success=True, message="Categoría actualizada", data=_to_response(cat))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    category_repo: CategoryRepository = Depends(get_category_repository),
):
    current_user = await require_role("ADMIN")(current_user)
    use_case = DeleteCategoryUseCase(category_repo)
    await use_case.execute(category_id)
    return None
