"""Review repository for MongoDB operations on reviews collection."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class ReviewRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "reviews")

    async def get_by_id(self, review_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"id": review_id})

    async def list_by_business(self, business_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        return await self.find_many(
            {"business_id": business_id},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def list_by_user(self, user_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        return await self.find_many(
            {"user_id": user_id},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def add_or_replace_review(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        # Enforce one review per user per business
        await self.delete_many({"business_id": doc["business_id"], "user_id": doc["user_id"]})
        return await self.insert_one(doc)

    async def delete_by_id(self, review_id: str) -> bool:
        return await self.delete_one({"id": review_id})

    async def delete_by_business_id(self, business_id: str) -> int:
        return await self.delete_many({"business_id": business_id})

    async def get_by_user_and_business(self, user_id: str, business_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"user_id": user_id, "business_id": business_id})

    async def update_reply(self, review_id: str, reply: str) -> bool:
        return await self.update_one({"id": review_id}, {"$set": {"owner_reply": reply}})

    async def list_by_business_ids(self, business_ids: List[str], limit: int = 500) -> List[Dict[str, Any]]:
        if not business_ids:
            return []
        return await self.find_many(
            {"business_id": {"$in": business_ids}},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def get_all_by_business(self, business_id: str) -> List[Dict[str, Any]]:
        return await self.find_many({"business_id": business_id}, limit=5000)
