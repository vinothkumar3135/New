"""Subscriptions API router."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_subscription_service
from app.schemas.subscription import PlanResponse, SubscribeIn, SubscriptionResponse
from app.services.subscription_service import SubscriptionService

router = APIRouter(tags=["Subscriptions"])

@router.get("/subscriptions/plans", response_model=List[PlanResponse])
@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """List all available subscription plans."""
    return subscription_service.get_plans()

@router.get("/subscriptions/me", response_model=SubscriptionResponse)
async def my_subscription(
    user: Dict[str, Any] = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get active subscription plan for current user."""
    return await subscription_service.get_my_subscription(user)

@router.post("/subscriptions/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    data: SubscribeIn,
    user: Dict[str, Any] = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Subscribe or switch plan."""
    return await subscription_service.subscribe(data.plan_id, user)

@router.post("/subscriptions/{plan_id}", response_model=SubscriptionResponse)
async def subscribe_by_path(
    plan_id: str,
    payload: Dict[str, Any] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Subscribe or switch plan by plan_id path param."""
    payload = payload or {}
    return await subscription_service.subscribe(
        plan_id=plan_id,
        current_user=user,
        payment_method=payload.get("payment_method", "free"),
        payment_reference=payload.get("upi_id") or payload.get("card_last4"),
    )
