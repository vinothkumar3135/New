"""Authentication dependencies for FastAPI route handlers."""

from typing import Any, Dict, Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.database.mongodb import get_database
from app.repositories.user_repository import UserRepository

security = HTTPBearer(auto_error=False)

async def get_user_repo(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserRepository:
    return UserRepository(db)

async def get_current_user(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Dict[str, Any]:
    """Validate JWT token and return authenticated user document."""
    if not cred:
        raise UnauthorizedException("Not authenticated")
    uid = decode_access_token(cred.credentials)
    if not uid:
        raise UnauthorizedException("Invalid token")
    user = await user_repo.get_by_id(uid, include_password=False)
    if not user:
        raise UnauthorizedException("User not found")
    return user

async def get_current_user_optional(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Optional[Dict[str, Any]]:
    """Return user document if token is valid, else None."""
    if not cred:
        return None
    uid = decode_access_token(cred.credentials)
    if not uid:
        return None
    return await user_repo.get_by_id(uid, include_password=False)
