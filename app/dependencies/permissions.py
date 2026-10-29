"""Role-based permission dependencies."""

from typing import Any, Callable, Dict
from fastapi import Depends
from app.core.exceptions import ForbiddenException
from app.dependencies.auth import get_current_user

def require_role(*roles: str) -> Callable:
    """Dependency factory that checks if the authenticated user has any of the specified roles."""
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role", "")
        if user_role not in roles:
            raise ForbiddenException(f"Requires role: {roles}")
        return user

    return role_checker
