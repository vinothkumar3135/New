"""Favorite service managing user bookmarked businesses."""

from typing import Any, Dict, List
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.business_repository import BusinessRepository
from app.schemas.business import BusinessResponse
from app.utils.response import normalize_business

class FavoriteService:
    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        business_repo: BusinessRepository,
    ):
        self.favorite_repo = favorite_repo
        self.business_repo = business_repo

    async def list_my_favorites(self, current_user: Dict[str, Any]) -> List[BusinessResponse]:
        favs = await self.favorite_repo.list_by_user(current_user["id"])
        ids = [f["business_id"] for f in favs]
        if not ids:
            return []
        businesses = await self.business_repo.find_many({"id": {"$in": ids}})
        for b in businesses:
            b["is_favorited"] = True
        return [BusinessResponse(**normalize_business(b)) for b in businesses]

    async def add_favorite(self, business_id: str, current_user: Dict[str, Any]) -> Dict[str, bool]:
        await self.favorite_repo.add_favorite(current_user["id"], business_id)
        return {"ok": True, "favorited": True, "saved": True}

    async def remove_favorite(self, business_id: str, current_user: Dict[str, Any]) -> Dict[str, bool]:
        await self.favorite_repo.remove_favorite(current_user["id"], business_id)
        return {"ok": True, "favorited": False, "saved": False}
