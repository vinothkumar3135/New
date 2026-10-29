"""Businesses API router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.dependencies.permissions import require_role
from app.dependencies.services import get_business_service
from app.schemas.business import (
    BusinessIn,
    BusinessUpdate,
    BusinessResponse,
    BusinessListResponse,
    BusinessDetailResponse,
)
from app.services.business_service import BusinessService

router = APIRouter(tags=["Businesses"])

@router.get("/locations")
async def list_locations(
    business_service: BusinessService = Depends(get_business_service),
):
    """Retrieve distinct operating cities and their prominent areas."""
    return await business_service.get_locations()

@router.get("/businesses", response_model=BusinessListResponse)
async def list_businesses(
    q: Optional[str] = None,
    category_id: Optional[str] = None,
    city: Optional[str] = None,
    min_rating: Optional[float] = None,
    verified: Optional[bool] = None,
    sort: Optional[str] = None,
    featured: Optional[bool] = None,
    near_lat: Optional[float] = None,
    near_lng: Optional[float] = None,
    radius_km: Optional[float] = 25.0,
    include_pending: Optional[bool] = False,
    limit: int = 24,
    skip: int = 0,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    business_service: BusinessService = Depends(get_business_service),
):
    """Search and filter businesses, including full-text search and Haversine geo-distance radius search."""
    return await business_service.list_businesses(
        q=q,
        category_id=category_id,
        city=city,
        min_rating=min_rating,
        verified=verified,
        sort=sort,
        featured=featured,
        near_lat=near_lat,
        near_lng=near_lng,
        radius_km=radius_km,
        include_pending=include_pending,
        limit=limit,
        skip=skip,
        current_user=user,
    )

@router.get("/businesses/owner/me", response_model=List[BusinessResponse])
@router.get("/owner/businesses", response_model=List[BusinessResponse])
async def my_businesses(
    user: Dict[str, Any] = Depends(require_role("business_owner", "admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Get all businesses owned by current authenticated business owner / admin."""
    return await business_service.get_my_businesses(user)

@router.get("/admin/pending-businesses")
async def pending_businesses(
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Retrieve all businesses pending moderation approval."""
    return await business_service.get_pending_businesses()

@router.post("/businesses/{bid}/events")
async def track_business_event(
    bid: str,
    kind: str = Query("view", description="Event kind: view, call, whatsapp, direction, website"),
    business_service: BusinessService = Depends(get_business_service),
):
    """Track client engagement events on a business profile."""
    return await business_service.track_event(bid, kind)

@router.get("/businesses/{bid}/reviews/eligibility")
async def check_review_eligibility(
    bid: str,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    business_service: BusinessService = Depends(get_business_service),
):
    """Check if the user is eligible to review this business."""
    return await business_service.get_review_eligibility(bid, user)

@router.get("/businesses/{slug}", response_model=BusinessDetailResponse)
async def get_business(
    slug: str,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    business_service: BusinessService = Depends(get_business_service),
):
    """Get business details by slug or UUID (supports both flat web and nested mobile contracts)."""
    return await business_service.get_business_by_slug_or_id(slug, user)

@router.post("/businesses", response_model=BusinessResponse)
async def create_business(
    data: BusinessIn,
    user: Dict[str, Any] = Depends(require_role("business_owner", "admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Create a new business listing. Owners land in pending status; admins are auto-approved."""
    return await business_service.create_business(data, user)

@router.put("/businesses/{bid}", response_model=BusinessResponse)
async def update_business(
    bid: str,
    data: BusinessUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    business_service: BusinessService = Depends(get_business_service),
):
    """Update business details (owner or admin only)."""
    return await business_service.update_business(bid, data, user)

@router.delete("/businesses/{bid}")
async def delete_business(
    bid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Delete a business and its associated reviews, favorites, and enquiries."""
    await business_service.delete_business(bid, user)
    return {"ok": True}

@router.post("/businesses/{bid}/verify", response_model=BusinessResponse)
async def verify_business(
    bid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Grant verified badge to a business."""
    return await business_service.verify_business(bid)

@router.post("/businesses/{bid}/approve", response_model=BusinessResponse)
async def approve_business(
    bid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Approve a pending business listing."""
    return await business_service.approve_business(bid)

@router.post("/businesses/{bid}/reject", response_model=BusinessResponse)
async def reject_business(
    bid: str,
    reason: str = Query("Does not meet our guidelines"),
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Reject a pending business listing with reason."""
    return await business_service.reject_business(bid, reason)

@router.post("/businesses/{bid}/feature", response_model=BusinessResponse)
async def feature_business(
    bid: str,
    user: Dict[str, Any] = Depends(require_role("admin")),
    business_service: BusinessService = Depends(get_business_service),
):
    """Admin-only: Toggle featured status of a business."""
    return await business_service.feature_business(bid)
