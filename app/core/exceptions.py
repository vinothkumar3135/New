"""Custom domain exceptions and error definitions for Infoez backend."""

from typing import Optional, Any
from fastapi import HTTPException, status

class AppException(HTTPException):
    """Base application exception with optional error code."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: Optional[str] = None,
        headers: Optional[dict] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code

class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, code=code)

class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authenticated", code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code=code,
            headers={"WWW-Authenticate": "Bearer"},
        )

class ForbiddenException(AppException):
    def __init__(self, detail: str = "Permission denied", code: str = "FORBIDDEN"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, code=code)

class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request", code: str = "BAD_REQUEST"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, code=code)

class ConflictException(AppException):
    def __init__(self, detail: str = "Conflict with existing resource", code: str = "CONFLICT"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, code=code)
