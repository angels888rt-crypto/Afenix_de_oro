"""Exception handlers for API."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared.exceptions import ApplicationException
from app.shared.responses import ErrorResponseSchema


def register_exception_handlers(app: FastAPI):
    """Register exception handlers."""
    
    @app.exception_handler(ApplicationException)
    async def application_exception_handler(request: Request, exc: ApplicationException):
        """Handle application exceptions."""
        error_response = ErrorResponseSchema(
            success=False,
            message=exc.message,
            error_code=exc.error_code,
            errors=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        error_response = ErrorResponseSchema(
            success=False,
            message="Error interno del servidor",
            error_code="INTERNAL_SERVER_ERROR",
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(),
        )
