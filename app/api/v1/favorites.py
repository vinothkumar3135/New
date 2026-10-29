"""Favorites API router."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_favorite_service
from app.schemas.business import BusinessResponse
from app.services.favorite_service import FavoriteService

router = APIRouter(tags=["Favorites"])

@router.get("/favorites/me", response_model=List[BusinessResponse])
@router.get("/favorites", response_model=List[BusinessResponse])
async def my_favorites(
    user: Dict[str, Any] = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    """List all businesses bookmarked by current user."""
    return await favorite_service.list_my_favorites(user)

@router.post("/favorites/{bid}")
async def add_favorite(
    bid: str,
    user: Dict[str, Any] = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    """Bookmark a business."""
    return await favorite_service.add_favorite(bid, user)

@router.delete("/favorites/{bid}")
async def remove_favorite(
    bid: str,
    user: Dict[str, Any] = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    """Remove bookmark from a business."""
    return await favorite_service.remove_favorite(bid, user)
