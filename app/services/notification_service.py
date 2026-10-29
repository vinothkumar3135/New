"""Notification service managing in-app notifications and read statuses."""

from typing import Any, Dict, List
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationResponse

class NotificationService:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def list_my_notifications(self, current_user: Dict[str, Any]) -> List[NotificationResponse]:
        items = await self.notification_repo.list_by_user(current_user["id"])
        results = []
        for item in items:
            body_val = item.get("body") or item.get("message") or ""
            type_val = item.get("type") or item.get("kind") or "notification"
            item["body"] = body_val
            item["message"] = body_val
            item["type"] = type_val
            item["kind"] = type_val
            results.append(NotificationResponse(**item))
        return results

    async def mark_read(self, notification_id: str, current_user: Dict[str, Any]) -> bool:
        return await self.notification_repo.mark_read(notification_id, current_user["id"])

    async def mark_all_read(self, current_user: Dict[str, Any]) -> bool:
        await self.notification_repo.mark_all_read(current_user["id"])
        return True
