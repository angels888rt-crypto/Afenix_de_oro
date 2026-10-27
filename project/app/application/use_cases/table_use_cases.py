"""Use cases for table management."""
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.repositories import TableRepository
from app.domain.entities import Table
from app.shared.exceptions import ValidationException, DuplicateResourceException
from app.shared.constants.enums import TableStatus


class CreateTableUseCase:
    """Use case for creating a table."""
    
    def __init__(self, table_repository: TableRepository):
        self.table_repository = table_repository
    
    async def execute(self, table_number: int, capacity: int, location: Optional[str] = None, created_by: Optional[int] = None) -> Table:
        """Create a new table."""
        # Validate input
        if capacity <= 0:
            raise ValidationException("La capacidad debe ser mayor a 0")
        
        # Check if table already exists, including soft-deleted rows
        existing = await self.table_repository.get_by_number(table_number, include_deleted=True)
        if existing and existing.deleted_at is None:
            raise DuplicateResourceException(f"La mesa {table_number} ya existe")

        table = Table(
            table_number=table_number,
            capacity=capacity,
            status=TableStatus.DISPONIBLE,
            location=location,
            created_by=created_by,
            updated_by=created_by,
        )

        if existing and existing.deleted_at is not None:
            return await self.table_repository.restore(table)

        try:
            return await self.table_repository.create(table)
        except IntegrityError as exc:
            message = str(exc.orig).lower() if exc.orig else ""
            if "table_number" in message or "tables.table_number" in message:
                raise DuplicateResourceException(f"La mesa {table_number} ya existe") from exc
            raise DuplicateResourceException("La mesa ya existe") from exc


class GetTableUseCase:
    """Use case for getting table information."""
    
    def __init__(self, table_repository: TableRepository):
        self.table_repository = table_repository
    
    async def execute(self, table_id: int) -> Table:
        """Get table by ID."""
        table = await self.table_repository.get_by_id(table_id)
        if not table:
            raise ValidationException("Mesa no encontrada")
        return table


class ListTablesUseCase:
    """Use case for listing tables."""
    
    def __init__(self, table_repository: TableRepository):
        self.table_repository = table_repository
    
    async def execute(self, skip: int = 0, limit: int = 10) -> list[Table]:
        """List tables."""
        return await self.table_repository.list(skip, limit)


class UpdateTableUseCase:
    """Use case for updating table."""
    
    def __init__(self, table_repository: TableRepository):
        self.table_repository = table_repository
    
    async def execute(self, table_id: int, capacity: Optional[int] = None, status: Optional[str] = None, location: Optional[str] = None, updated_by: Optional[int] = None) -> Table:
        """Update table."""
        table = await self.table_repository.get_by_id(table_id)
        if not table:
            raise ValidationException("Mesa no encontrada")
        
        if capacity is not None and capacity <= 0:
            raise ValidationException("La capacidad debe ser mayor a 0")
        
        if status:
            valid_statuses = [s.value for s in TableStatus]
            if status not in valid_statuses:
                raise ValidationException(f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}")
        
        table.capacity = capacity or table.capacity
        table.status = status or table.status
        table.location = location if location is not None else table.location
        table.updated_by = updated_by
        
        return await self.table_repository.update(table_id, table)


class DeleteTableUseCase:
    """Use case for deleting table."""
    
    def __init__(self, table_repository: TableRepository):
        self.table_repository = table_repository
    
    async def execute(self, table_id: int) -> bool:
        """Delete table."""
        table = await self.table_repository.get_by_id(table_id)
        if not table:
            raise ValidationException("Mesa no encontrada")
        return await self.table_repository.delete(table_id)


class GetAvailableTablesUseCase:
    """Use case for getting available tables."""
    
    def __init__(self, table_repository: TableRepository):
        self.table_repository = table_repository
    
    async def execute(self, skip: int = 0, limit: int = 10) -> list[Table]:
        """Get available tables."""
        return await self.table_repository.get_by_status(TableStatus.DISPONIBLE.value, skip, limit)


class GetTableByNumberUseCase:
    """Use case for getting table by number."""
    
    def __init__(self, table_repository: TableRepository):
        self.table_repository = table_repository
    
    async def execute(self, table_number: int) -> Table:
        """Get table by number."""
        table = await self.table_repository.get_by_number(table_number)
        if not table:
            raise ValidationException(f"Mesa {table_number} no encontrada")
        return table
