"""Business repository for MongoDB operations on businesses collection."""

from typing import Any, Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class BusinessRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "businesses")

    async def get_by_id(self, business_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"id": business_id})

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"slug": slug})

    async def get_by_slug_or_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        doc = await self.find_one({"slug": identifier})
        if not doc:
            doc = await self.find_one({"id": identifier})
        return doc

    async def create_business(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_one(doc)

    async def update_business(self, business_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if fields:
            await self.update_one({"id": business_id}, {"$set": fields})
        return await self.get_by_id(business_id)

    async def increment_view_count(self, business_id: str) -> None:
        await self.update_one({"id": business_id}, {"$inc": {"view_count": 1}})

    async def update_rating(self, business_id: str, avg_rating: float, count: int) -> None:
        await self.update_one(
            {"id": business_id},
            {"$set": {"rating": round(avg_rating, 1), "review_count": count}},
        )

    async def delete_business(self, business_id: str) -> bool:
        return await self.delete_one({"id": business_id})

    async def get_owner_businesses(self, owner_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        return await self.find_many({"owner_id": owner_id}, limit=limit)

    async def get_pending_businesses(self, limit: int = 500) -> List[Dict[str, Any]]:
        return await self.find_many({"status": "pending"}, sort=[("created_at", -1)], limit=limit)
