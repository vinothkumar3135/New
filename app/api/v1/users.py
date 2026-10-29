"""Admin user management and system statistics API router."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_role
from app.dependencies.services import get_user_service, get_business_service
from app.schemas.business import BusinessResponse
from app.schemas.user import UserResponse
from app.services.business_service import BusinessService
from app.services.user_service import UserService

router = APIRouter(tags=["Admin & Users"])

@router.get("/admin/stats")
@router.get("/admin/overview")
async def admin_stats(
    user: Dict[str, Any] = Depends(require_role("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Admin-only: Retrieve high-level directory metrics."""
    return await user_service.get_stats()

@router.get("/admin/users", response_model=List[UserResponse])
async def admin_users(
    user: Dict[str, Any] = Depends(require_role("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Admin-only: List all registered users."""
    return await user_service.list_users()

@router.get("/admin/businesses", response_model=List[BusinessResponse])
async def admin_businesses(
    status_filter: str = "pending",
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Filter and retrieve businesses by status (e.g. pending, active, rejected)."""
    res = await business_service.list_businesses(
        include_pending=True,
        limit=200,
        current_user=user,
    )
    return [b for b in res.items if b.status == status_filter]

@router.patch("/admin/businesses/{bid}")
async def moderate_business(
    bid: str,
    decision: str = "approved",
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Moderate business (approved or rejected)."""
    if decision == "approved":
        await business_service.approve_business(bid)
    else:
        await business_service.reject_business(bid, reason="Rejected by admin moderation")
    return {"message": f"Business {decision} successfully", "ok": True}

@router.patch("/admin/users/{uid}")
async def moderate_user(
    uid: str,
    status: str = "active",
    user: Dict[str, Any] = Depends(require_role("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Admin-only: Moderate user status (active or suspended)."""
    await user_service.update_status(uid, status)
    return {"message": f"User status set to {status}", "ok": True}

@router.patch("/admin/users/{uid}/role")
async def admin_set_role(
    uid: str,
    role: str = Query(..., description="Target role: customer, business_owner, or admin"),
    user: Dict[str, Any] = Depends(require_role("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Admin-only: Update role of a specific user."""
    await user_service.update_role(uid, role)
    return {"ok": True}

@router.delete("/admin/users/{uid}")
async def admin_delete_user(
    uid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Admin-only: Delete a user by ID."""
    await user_service.delete_user(uid, user["id"])
    return {"ok": True}
