"""Category repository for MongoDB operations on categories collection."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class CategoryRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "categories")

    async def list_categories(self, limit: int = 500) -> List[Dict[str, Any]]:
        return await self.find_many(limit=limit)

    async def get_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"id": category_id})

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"slug": slug})

    async def create_category(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_one(doc)

    async def toggle_active(self, category_id: str) -> Optional[bool]:
        cat = await self.get_by_id(category_id)
        if not cat:
            return None
        new_active = not bool(cat.get("is_active", True))
        await self.update_one({"id": category_id}, {"$set": {"is_active": new_active}})
        return new_active

    async def delete_category(self, category_id: str) -> bool:
        return await self.delete_one({"id": category_id})
