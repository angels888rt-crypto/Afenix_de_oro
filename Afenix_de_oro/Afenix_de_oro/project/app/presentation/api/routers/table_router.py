"""Table API routers."""
from fastapi import APIRouter, Depends, status, Query

from app.infrastructure.database.repositories import TableRepository
from app.application.use_cases.table_use_cases import (
    CreateTableUseCase, GetTableUseCase, ListTablesUseCase, UpdateTableUseCase,
    DeleteTableUseCase, GetAvailableTablesUseCase, GetTableByNumberUseCase
)
from app.application.dto import TableCreateRequest, TableUpdateRequest, TableResponse
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_table_repository, get_current_user, require_role
)

router = APIRouter(prefix="/api/v1/tables", tags=["Tables"])


@router.post("", response_model=ResponseSchema[TableResponse], status_code=status.HTTP_201_CREATED)
async def create_table(
    request: TableCreateRequest,
    current_user: dict = Depends(get_current_user),
    table_repository: TableRepository = Depends(get_table_repository),
):
    """
    Create a new table (admin only).
    
    - **table_number**: Unique table number
    - **capacity**: Table capacity (> 0)
    - **location**: Optional location description
    """
    current_user = await require_role("ADMIN")(current_user)
    use_case = CreateTableUseCase(table_repository)
    table = await use_case.execute(
        table_number=request.table_number,
        capacity=request.capacity,
        location=request.location,
        created_by=current_user["user_id"],
    )
    
    return ResponseSchema(
        success=True,
        message="Mesa creada exitosamente",
        data=TableResponse(
            id=table.id,
            table_number=table.table_number,
            capacity=table.capacity,
            status=table.status,
            location=table.location,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )
    )


@router.get("/{table_id}", response_model=ResponseSchema[TableResponse])
async def get_table(
    table_id: int,
    current_user: dict = Depends(get_current_user),
    table_repository: TableRepository = Depends(get_table_repository),
):
    """Get table by ID."""
    use_case = GetTableUseCase(table_repository)
    table = await use_case.execute(table_id)
    
    return ResponseSchema(
        success=True,
        message="Mesa obtenida exitosamente",
        data=TableResponse(
            id=table.id,
            table_number=table.table_number,
            capacity=table.capacity,
            status=table.status,
            location=table.location,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )
    )


@router.get("", response_model=ResponseSchema[list[TableResponse]])
async def list_tables(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    table_repository: TableRepository = Depends(get_table_repository),
):
    """List all tables."""
    use_case = ListTablesUseCase(table_repository)
    tables = await use_case.execute(skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Mesas obtenidas exitosamente",
        data=[
            TableResponse(
                id=table.id,
                table_number=table.table_number,
                capacity=table.capacity,
                status=table.status,
                location=table.location,
                created_at=table.created_at,
                updated_at=table.updated_at,
            )
            for table in tables
        ]
    )


@router.put("/{table_id}", response_model=ResponseSchema[TableResponse])
async def update_table(
    table_id: int,
    request: TableUpdateRequest,
    current_user: dict = Depends(get_current_user),
    table_repository: TableRepository = Depends(get_table_repository),
):
    """Update table (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = UpdateTableUseCase(table_repository)
    table = await use_case.execute(
        table_id=table_id,
        capacity=request.capacity,
        status=request.status,
        location=request.location,
        updated_by=current_user["user_id"],
    )
    
    return ResponseSchema(
        success=True,
        message="Mesa actualizada exitosamente",
        data=TableResponse(
            id=table.id,
            table_number=table.table_number,
            capacity=table.capacity,
            status=table.status,
            location=table.location,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )
    )


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(
    table_id: int,
    current_user: dict = Depends(get_current_user),
    table_repository: TableRepository = Depends(get_table_repository),
):
    """Delete table (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = DeleteTableUseCase(table_repository)
    await use_case.execute(table_id)


@router.get("/available/list", response_model=ResponseSchema[list[TableResponse]])
async def get_available_tables(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    table_repository: TableRepository = Depends(get_table_repository),
):
    """Get available tables."""
    use_case = GetAvailableTablesUseCase(table_repository)
    tables = await use_case.execute(skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Mesas disponibles obtenidas exitosamente",
        data=[
            TableResponse(
                id=table.id,
                table_number=table.table_number,
                capacity=table.capacity,
                status=table.status,
                location=table.location,
                created_at=table.created_at,
                updated_at=table.updated_at,
            )
            for table in tables
        ]
    )


@router.get("/number/{table_number}", response_model=ResponseSchema[TableResponse])
async def get_table_by_number(
    table_number: int,
    current_user: dict = Depends(get_current_user),
    table_repository: TableRepository = Depends(get_table_repository),
):
    """Get table by table number."""
    use_case = GetTableByNumberUseCase(table_repository)
    table = await use_case.execute(table_number)
    
    return ResponseSchema(
        success=True,
        message="Mesa obtenida exitosamente",
        data=TableResponse(
            id=table.id,
            table_number=table.table_number,
            capacity=table.capacity,
            status=table.status,
            location=table.location,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )
    )
