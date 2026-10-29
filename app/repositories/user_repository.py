"""User repository for MongoDB operations on users collection."""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "users")

    async def get_by_id(self, user_id: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
        proj = {"_id": 0} if include_password else {"_id": 0, "password": 0}
        return await self.find_one({"id": user_id}, projection=proj)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        # In MongoDB find_one with password so auth_service can verify credentials
        return await self.find_one({"email": email.lower().strip()}, projection={"_id": 0})

    async def create_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return await self.insert_one(user)

    async def update_profile(self, user_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if fields:
            await self.update_one({"id": user_id}, {"$set": fields})
        return await self.get_by_id(user_id)

    async def update_role(self, user_id: str, role: str) -> bool:
        return await self.update_one({"id": user_id}, {"$set": {"role": role}})

    async def update_status(self, user_id: str, status: str) -> bool:
        return await self.update_one({"id": user_id}, {"$set": {"status": status}})

    async def delete_by_id(self, user_id: str) -> bool:
        return await self.delete_one({"id": user_id})

    async def get_all_users(self, limit: int = 1000) -> List[Dict[str, Any]]:
        return await self.find_many(
            projection={"_id": 0, "password": 0},
            sort=[("created_at", -1)],
            limit=limit,
        )

    async def get_admins(self) -> List[Dict[str, Any]]:
        return await self.find_many({"role": "admin"}, projection={"_id": 0, "id": 1})
