"""Subscription repository for MongoDB operations on subscriptions collection."""

from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class SubscriptionRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "subscriptions")

    async def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"user_id": user_id})

    async def save_subscription(self, user_id: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        await self.delete_many({"user_id": user_id})
        return await self.insert_one(doc)
