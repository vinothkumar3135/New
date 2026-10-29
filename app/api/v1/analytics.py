"""Analytics API router for business owners."""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from app.dependencies.permissions import require_role
from app.dependencies.services import get_analytics_service
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Analytics"])

@router.get("/owner/analytics")
async def owner_analytics(
    user: Dict[str, Any] = Depends(require_role("business_owner", "admin")),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Retrieve performance statistics for business owner dashboard."""
    return await analytics_service.get_owner_analytics(user)

@router.get("/owner/analytics/trends")
async def owner_analytics_trends(
    user: Dict[str, Any] = Depends(require_role("business_owner", "admin")),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Retrieve 7-day trend metrics for business owner dashboard."""
    return await analytics_service.get_owner_trends(user)
