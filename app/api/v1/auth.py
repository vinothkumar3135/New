"""Authentication API router."""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_auth_service
from app.schemas.auth import RegisterIn, LoginIn, TokenResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])

@router.post("/auth/register", response_model=TokenResponse)
async def register(
    data: RegisterIn,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new customer or business owner account."""
    return await auth_service.register(data)

@router.post("/auth/login", response_model=TokenResponse)
async def login(
    data: LoginIn,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password to receive a JWT access token."""
    return await auth_service.login(data)

@router.get("/auth/me", response_model=UserResponse)
async def me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Fetch current logged-in user profile."""
    return await auth_service.get_me(current_user)

@router.patch("/auth/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Update current user profile attributes."""
    return await auth_service.update_me(current_user, data)
