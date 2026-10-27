"""Response schema for API responses."""
from typing import Any, Optional, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    """Standard response schema for successful operations."""
    
    success: bool = Field(
        default=True,
        description="Indica si la operación fue exitosa"
    )
    message: str = Field(
        default="Operación exitosa",
        description="Mensaje descriptivo de la operación"
    )
    data: Optional[T] = Field(
        default=None,
        description="Datos de la respuesta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operación exitosa",
                "data": {}
            }
        }


class ErrorResponseSchema(BaseModel):
    """Standard response schema for error operations."""
    
    success: bool = Field(
        default=False,
        description="Indica que ocurrió un error"
    )
    message: str = Field(
        description="Mensaje descriptivo del error"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Código de error interno"
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detalles específicos del error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Descripción del error",
                "error_code": "ERROR_CODE",
                "errors": []
            }
        }
