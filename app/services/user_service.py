"""User management service for admin controls and user stats."""

from typing import Any, Dict, List
from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.user_repository import UserRepository
from app.repositories.business_repository import BusinessRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.enquiry_repository import EnquiryRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.user import UserResponse
from app.utils.response import normalize_user

class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        business_repo: BusinessRepository,
        review_repo: ReviewRepository,
        enquiry_repo: EnquiryRepository,
        claim_repo: ClaimRepository,
        category_repo: CategoryRepository,
    ):
        self.user_repo = user_repo
        self.business_repo = business_repo
        self.review_repo = review_repo
        self.enquiry_repo = enquiry_repo
        self.claim_repo = claim_repo
        self.category_repo = category_repo

    async def list_users(self) -> List[UserResponse]:
        docs = await self.user_repo.get_all_users()
        return [UserResponse(**normalize_user(d)) for d in docs]

    async def update_role(self, user_id: str, role: str) -> bool:
        if role not in ("customer", "business_owner", "admin"):
            raise BadRequestException("Invalid role")
        updated = await self.user_repo.update_role(user_id, role)
        if not updated:
            raise NotFoundException("User not found")
        return True

    async def update_status(self, user_id: str, status: str) -> bool:
        if status not in ("active", "suspended"):
            raise BadRequestException("Invalid status")
        updated = await self.user_repo.update_status(user_id, status)
        if not updated:
            raise NotFoundException("User not found")
        return True

    async def delete_user(self, target_user_id: str, current_user_id: str) -> bool:
        if target_user_id == current_user_id:
            raise BadRequestException("Cannot delete self")
        deleted = await self.user_repo.delete_by_id(target_user_id)
        if not deleted:
            raise NotFoundException("User not found")
        return True

    async def get_stats(self) -> Dict[str, int]:
        return {
            "users": await self.user_repo.count_documents({}),
            "businesses": await self.business_repo.count_documents({}),
            "pending_businesses": await self.business_repo.count_documents({"status": "pending"}),
            "verified_businesses": await self.business_repo.count_documents({"verified": True}),
            "reviews": await self.review_repo.count_documents({}),
            "enquiries": await self.enquiry_repo.count_documents({}),
            "pending_claims": await self.claim_repo.count_documents({"status": "pending"}),
            "categories": await self.category_repo.count_documents({}),
        }
