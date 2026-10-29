"""Category management service."""

from typing import Any, Dict, List
from app.core.exceptions import NotFoundException
from app.repositories.category_repository import CategoryRepository
from app.repositories.business_repository import BusinessRepository
from app.schemas.category import CategoryIn, CategoryResponse
from app.utils.datetime import new_id, now_iso
from app.utils.slug import slugify

class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepository,
        business_repo: BusinessRepository,
    ):
        self.category_repo = category_repo
        self.business_repo = business_repo

    async def list_categories(self, include_inactive: bool = False) -> List[CategoryResponse]:
        cats = await self.category_repo.list_categories()
        results = []
        for c in cats:
            is_active = bool(c.get("is_active", True))
            if not include_inactive and not is_active:
                continue
            count = await self.business_repo.count_documents({
                "category_id": c["id"],
                "status": "active",
            })
            c["business_count"] = count
            c["is_active"] = is_active
            results.append(CategoryResponse(**c))
        return results

    async def create_category(self, data: CategoryIn) -> CategoryResponse:
        doc = {
            "id": new_id(),
            "name": data.name,
            "slug": slugify(data.name),
            "icon": data.icon or "Store",
            "color": data.color or "#D97706",
            "description": data.description or "",
            "is_active": True,
            "sort_order": 1,
            "created_at": now_iso(),
        }
        await self.category_repo.create_category(doc)
        doc["business_count"] = 0
        return CategoryResponse(**doc)

    async def toggle_category(self, category_id: str) -> Dict[str, Any]:
        new_active = await self.category_repo.toggle_active(category_id)
        if new_active is None:
            raise NotFoundException("Category not found")
        return {"is_active": new_active, "ok": True}

    async def delete_category(self, category_id: str) -> bool:
        return await self.category_repo.delete_category(category_id)
