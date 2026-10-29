"""Enquiry repository for MongoDB operations on enquiries collection."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class EnquiryRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "enquiries")

    async def create_enquiry(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_one(doc)

    async def list_by_user(self, user_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        return await self.find_many(
            {"user_id": user_id},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def list_by_business_ids(self, business_ids: List[str], limit: int = 1000) -> List[Dict[str, Any]]:
        if not business_ids:
            return []
        return await self.find_many(
            {"business_id": {"$in": business_ids}},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def get_by_id(self, enquiry_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"id": enquiry_id})

    async def update_lead(self, enquiry_id: str, status: Optional[str] = None, notes: Optional[str] = None) -> bool:
        update_fields: Dict[str, Any] = {}
        if status is not None:
            update_fields["status"] = status
        if notes is not None:
            update_fields["notes"] = notes
        if not update_fields:
            return True
        return await self.update_one({"id": enquiry_id}, {"$set": update_fields})

    async def delete_by_business_id(self, business_id: str) -> int:
        return await self.delete_many({"business_id": business_id})
