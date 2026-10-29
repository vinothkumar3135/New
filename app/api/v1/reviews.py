"""Reviews API router."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_review_service
from app.schemas.review import ReviewIn, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(tags=["Reviews"])

@router.get("/businesses/{bid}/reviews", response_model=List[ReviewResponse])
async def list_business_reviews(
    bid: str,
    review_service: ReviewService = Depends(get_review_service),
):
    """List all reviews for a business."""
    return await review_service.list_reviews_for_business(bid)

@router.post("/businesses/{bid}/reviews", response_model=ReviewResponse)
async def add_review(
    bid: str,
    data: ReviewIn,
    user: Dict[str, Any] = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Submit or update a review (1-5 stars) on a business."""
    return await review_service.add_review(bid, data, user)

@router.get("/reviews/me", response_model=List[ReviewResponse])
async def my_reviews(
    user: Dict[str, Any] = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """List all reviews submitted by current user."""
    return await review_service.list_my_reviews(user)

@router.get("/owner/reviews", response_model=List[ReviewResponse])
async def owner_reviews(
    user: Dict[str, Any] = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """List all reviews received across businesses owned by current user."""
    return await review_service.list_owner_reviews(user)

@router.post("/reviews/{rid}/reply")
async def reply_review(
    rid: str,
    reply: str = "",
    user: Dict[str, Any] = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Post an owner reply to a customer review."""
    return await review_service.reply_review(rid, reply, user)

@router.delete("/reviews/{rid}")
async def delete_review(
    rid: str,
    user: Dict[str, Any] = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Delete a review (author or admin only)."""
    await review_service.delete_review(rid, user)
    return {"ok": True}
