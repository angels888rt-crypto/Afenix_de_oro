"""Subcategory API routers."""
from fastapi import APIRouter, Depends, status, Query
from app.infrastructure.database.repositories import SubcategoryRepository
from app.application.use_cases.subcategory_use_cases import (
    CreateSubcategoryUseCase, ListSubcategoriesUseCase, GetSubcategoryUseCase, UpdateSubcategoryUseCase, DeleteSubcategoryUseCase,
    CreateOptionUseCase, UpdateOptionUseCase, DeleteOptionUseCase, ListOptionsUseCase
)
from app.application.dto import SubcategoryCreateRequest, SubcategoryUpdateRequest, SubcategoryResponse, SubcategoryOptionResponse, SubcategoryOptionCreateRequest, SubcategoryOptionUpdateRequest
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import get_subcategory_repository, get_current_user, require_role

router = APIRouter(prefix="/api/v1/subcategories", tags=["Subcategories"])

def _to_option_response(opt) -> SubcategoryOptionResponse:
    return SubcategoryOptionResponse(id=opt.id, subcategory_id=opt.subcategory_id, name=opt.name, created_at=opt.created_at, updated_at=opt.updated_at)

def _to_response(sub) -> SubcategoryResponse:
    opts = [_to_option_response(o) for o in (sub.options or [])]
    dishes = [{"id": did, "name": ""} for did in (sub.dish_ids or [])]  # names filled via frontend if needed, but we can leave empty.
    # To enrich dish names, we could fetch but keep simple; frontend will fetch dish list.
    # Instead we provide dish_ids; dishes names will be resolved via separate dish fetch.
    # For richer response, we could fetch dish names via repository but keep ids for now.
    return SubcategoryResponse(id=sub.id, name=sub.name, description=sub.description, options=opts, dish_ids=sub.dish_ids or [], dishes=dishes, created_at=sub.created_at, updated_at=sub.updated_at)

# helper to enrich dishes names
async def _enrich_with_dish_names(subs, sub_repo):
    # subs is list of Subcategory domain with dish_ids; we want to populate dishes names
    # fetch dish names via session query
    from sqlalchemy import select
    from app.infrastructure.database.models import DishModel
    enriched=[]
    for sub in subs:
        resp = _to_response(sub)
        if sub.dish_ids:
            try:
                result = await sub_repo.session.execute(select(DishModel.id, DishModel.name).where(DishModel.id.in_(sub.dish_ids), DishModel.deleted_at.is_(None)))
                rows = result.all()
                resp.dishes = [{"id": r[0], "name": r[1]} for r in rows]
            except Exception:
                resp.dishes = [{"id": did, "name": f"Plato #{did}"} for did in sub.dish_ids]
        enriched.append(resp)
    return enriched

@router.get("", response_model=ResponseSchema[list[SubcategoryResponse]])
async def list_subcategories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    sub_repo: SubcategoryRepository = Depends(get_subcategory_repository),
):
    use = ListSubcategoriesUseCase(sub_repo)
    subs = await use.execute(skip, limit)
    enriched = await _enrich_with_dish_names(subs, sub_repo)
    return ResponseSchema(success=True, message="Subcategorías obtenidas", data=enriched)

@router.get("/{sub_id}", response_model=ResponseSchema[SubcategoryResponse])
async def get_subcategory(sub_id:int, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    use = GetSubcategoryUseCase(sub_repo)
    sub = await use.execute(sub_id)
    enriched = await _enrich_with_dish_names([sub], sub_repo)
    return ResponseSchema(success=True, message="Subcategoría obtenida", data=enriched[0])

@router.post("", response_model=ResponseSchema[SubcategoryResponse], status_code=status.HTTP_201_CREATED)
async def create_subcategory(request: SubcategoryCreateRequest, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    current_user = await require_role("ADMIN")(current_user)
    use = CreateSubcategoryUseCase(sub_repo)
    sub = await use.execute(name=request.name, description=request.description, dish_ids=request.dish_ids, options=request.options, created_by=current_user["user_id"])
    enriched = await _enrich_with_dish_names([sub], sub_repo)
    return ResponseSchema(success=True, message="Subcategoría creada", data=enriched[0])

@router.put("/{sub_id}", response_model=ResponseSchema[SubcategoryResponse])
async def update_subcategory(sub_id:int, request: SubcategoryUpdateRequest, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    current_user = await require_role("ADMIN")(current_user)
    use = UpdateSubcategoryUseCase(sub_repo)
    sub = await use.execute(sub_id=sub_id, name=request.name, description=request.description, dish_ids=request.dish_ids, updated_by=current_user["user_id"])
    enriched = await _enrich_with_dish_names([sub], sub_repo)
    return ResponseSchema(success=True, message="Subcategoría actualizada", data=enriched[0])

@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcategory(sub_id:int, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    current_user = await require_role("ADMIN")(current_user)
    use = DeleteSubcategoryUseCase(sub_repo)
    await use.execute(sub_id)
    return None

# Options

@router.get("/{sub_id}/options", response_model=ResponseSchema[list[SubcategoryOptionResponse]])
async def list_options(sub_id:int, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    use = ListOptionsUseCase(sub_repo)
    opts = await use.execute(sub_id)
    return ResponseSchema(success=True, message="Opciones obtenidas", data=[_to_option_response(o) for o in opts])

@router.post("/{sub_id}/options", response_model=ResponseSchema[SubcategoryOptionResponse], status_code=status.HTTP_201_CREATED)
async def create_option(sub_id:int, request: SubcategoryOptionCreateRequest, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    current_user = await require_role("ADMIN")(current_user)
    use = CreateOptionUseCase(sub_repo)
    opt = await use.execute(sub_id=sub_id, name=request.name, created_by=current_user["user_id"])
    return ResponseSchema(success=True, message="Opción creada", data=_to_option_response(opt))

@router.put("/{sub_id}/options/{option_id}", response_model=ResponseSchema[SubcategoryOptionResponse])
async def update_option(sub_id:int, option_id:int, request: SubcategoryOptionUpdateRequest, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    current_user = await require_role("ADMIN")(current_user)
    if not request.name:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Nombre requerido")
    use = UpdateOptionUseCase(sub_repo)
    opt = await use.execute(sub_id=sub_id, option_id=option_id, name=request.name, updated_by=current_user["user_id"])
    return ResponseSchema(success=True, message="Opción actualizada", data=_to_option_response(opt))

@router.delete("/{sub_id}/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(sub_id:int, option_id:int, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    current_user = await require_role("ADMIN")(current_user)
    use = DeleteOptionUseCase(sub_repo)
    await use.execute(sub_id, option_id)
    return None

# Helper endpoint: get subcategories for a dish (for mesero)
@router.get("/dish/{dish_id}", response_model=ResponseSchema[list[SubcategoryResponse]])
async def get_subcategories_for_dish(dish_id:int, current_user: dict = Depends(get_current_user), sub_repo: SubcategoryRepository = Depends(get_subcategory_repository)):
    subs = await sub_repo.get_subcategories_for_dish(dish_id)
    enriched = await _enrich_with_dish_names(subs, sub_repo)
    return ResponseSchema(success=True, message="Subcategorías del plato", data=enriched)
