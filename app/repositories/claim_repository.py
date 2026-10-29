"""Claim repository for MongoDB operations on claims collection."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class ClaimRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "claims")

    async def create_claim(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_one(doc)

    async def get_by_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"id": claim_id})

    async def find_pending(self, business_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({
            "business_id": business_id,
            "user_id": user_id,
            "status": "pending",
        })

    async def list_by_user(self, user_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        return await self.find_many(
            {"user_id": user_id},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def list_all(self, limit: int = 500) -> List[Dict[str, Any]]:
        return await self.find_many(sort=[("created_at", -1)], limit=limit)

    async def update_status(self, claim_id: str, status: str) -> bool:
        return await self.update_one({"id": claim_id}, {"$set": {"status": status}})
