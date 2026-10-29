"""Categories API router."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.dependencies.permissions import require_role
from app.dependencies.services import get_category_service
from app.schemas.category import CategoryIn, CategoryResponse
from app.services.category_service import CategoryService

router = APIRouter(tags=["Categories"])

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    include_inactive: bool = False,
    category_service: CategoryService = Depends(get_category_service),
):
    """List all categories with live count of active businesses."""
    return await category_service.list_categories(include_inactive=include_inactive)

@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    data: CategoryIn,
    user: Dict[str, Any] = Depends(require_role("admin")),
    category_service: CategoryService = Depends(get_category_service),
):
    """Admin-only: Create a new category."""
    return await category_service.create_category(data)

@router.patch("/categories/{cid}/toggle")
async def toggle_category(
    cid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    category_service: CategoryService = Depends(get_category_service),
):
    """Admin-only: Toggle active status of a category."""
    return await category_service.toggle_category(cid)

@router.delete("/categories/{cid}")
async def delete_category(
    cid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    category_service: CategoryService = Depends(get_category_service),
):
    """Admin-only: Delete a category by ID."""
    await category_service.delete_category(cid)
    return {"ok": True}
