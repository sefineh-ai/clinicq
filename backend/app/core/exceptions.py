from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger("clinicq.exceptions")


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: list | None = None,
        headers: dict | None = None,
    ):
        self.message = message
        self.detail = message
        self.status_code = status_code
        self.errors = errors
        self.headers = headers
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict detected with existing resource"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", headers: dict | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers or {"WWW-Authenticate": "Bearer"},
        )


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", errors: list | None = None):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, errors=errors)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    payload = {"detail": exc.message}
    if exc.errors:
        payload["errors"] = exc.errors
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError | ValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field_path = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        errors.append({
            "field": field_path or "root",
            "message": err.get("msg", "Invalid value"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error. Please verify input fields.",
            "errors": errors,
        },
    )
