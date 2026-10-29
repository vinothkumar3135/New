"""Notification repository for MongoDB operations on notifications collection."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class NotificationRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "notifications")

    async def create_notification(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_one(doc)

    async def list_by_user(self, user_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        return await self.find_many(
            {"user_id": user_id},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def mark_read(self, notification_id: str, user_id: str) -> bool:
        return await self.update_one(
            {"id": notification_id, "user_id": user_id},
            {"$set": {"read": True}},
        )

    async def mark_all_read(self, user_id: str) -> int:
        return await self.update_many(
            {"user_id": user_id},
            {"$set": {"read": True}},
        )
