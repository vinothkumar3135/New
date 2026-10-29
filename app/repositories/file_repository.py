"""File repository for uploaded files metadata in MongoDB."""

from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class FileRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "files")

    async def create_file_record(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_one(doc)

    async def get_by_path(self, storage_path: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"storage_path": storage_path, "is_deleted": False})
