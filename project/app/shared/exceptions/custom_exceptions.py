"""Custom exceptions for the application."""
from typing import Any, Optional


class ApplicationException(Exception):
    """Base exception for application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []
        super().__init__(self.message)


class ValidationException(ApplicationException):
    """Raised when validation fails."""
    
    def __init__(
        self,
        message: str,
        details: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class ResourceNotFoundException(ApplicationException):
    """Raised when resource is not found."""
    
    def __init__(self, message: str = "Recurso no encontrado") -> None:
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
        )


class AuthenticationException(ApplicationException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Autenticación requerida") -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationException(ApplicationException):
    """Raised when user is not authorized."""
    
    def __init__(self, message: str = "No tiene permisos para realizar esta acción") -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
        )


class DuplicateResourceException(ApplicationException):
    """Raised when resource already exists."""
    
    def __init__(self, message: str = "El recurso ya existe") -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="DUPLICATE_RESOURCE",
        )


class ConflictException(ApplicationException):
    """Raised when operation conflicts with current state."""
    
    def __init__(self, message: str = "Operación no permitida en el estado actual") -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )
