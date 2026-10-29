"""Favorite repository for MongoDB operations on favorites collection."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository
from app.utils.datetime import new_id, now_iso

class FavoriteRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "favorites")

    async def list_by_user(self, user_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        return await self.find_many({"user_id": user_id}, limit=limit)

    async def is_favorited(self, user_id: str, business_id: str) -> bool:
        doc = await self.find_one({"user_id": user_id, "business_id": business_id})
        return bool(doc)

    async def add_favorite(self, user_id: str, business_id: str) -> bool:
        exists = await self.is_favorited(user_id, business_id)
        if not exists:
            await self.insert_one({
                "id": new_id(),
                "user_id": user_id,
                "business_id": business_id,
                "created_at": now_iso(),
            })
        return True

    async def remove_favorite(self, user_id: str, business_id: str) -> bool:
        return await self.delete_one({"user_id": user_id, "business_id": business_id})

    async def delete_by_business_id(self, business_id: str) -> int:
        return await self.delete_many({"business_id": business_id})
