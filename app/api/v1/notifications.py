"""Notifications API router."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_notification_service
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(tags=["Notifications"])

@router.get("/notifications/me", response_model=List[NotificationResponse])
@router.get("/notifications", response_model=List[NotificationResponse])
async def my_notifications(
    user: Dict[str, Any] = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """List in-app notifications for current user."""
    return await notification_service.list_my_notifications(user)

@router.patch("/notifications/{nid}/read")
async def mark_read(
    nid: str,
    user: Dict[str, Any] = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Mark a notification as read."""
    await notification_service.mark_read(nid, user)
    return {"ok": True, "read": True}

@router.post("/notifications/read-all")
async def mark_all_read(
    user: Dict[str, Any] = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read."""
    await notification_service.mark_all_read(user)
    return {"ok": True}
