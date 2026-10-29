"""Review service managing customer reviews, ratings recalculation, and review deletion."""

from typing import Any, Dict, List
from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.review_repository import ReviewRepository
from app.repositories.business_repository import BusinessRepository
from app.repositories.user_repository import UserRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.review import ReviewIn, ReviewResponse
from app.utils.datetime import new_id, now_iso

class ReviewService:
    def __init__(
        self,
        review_repo: ReviewRepository,
        business_repo: BusinessRepository,
        user_repo: UserRepository,
        notification_repo: NotificationRepository,
    ):
        self.review_repo = review_repo
        self.business_repo = business_repo
        self.user_repo = user_repo
        self.notification_repo = notification_repo

    async def list_reviews_for_business(self, business_id: str) -> List[ReviewResponse]:
        reviews = await self.review_repo.list_by_business(business_id)
        results = []
        for r in reviews:
            u = await self.user_repo.get_by_id(r["user_id"])
            r["user"] = {"name": u["name"], "avatar": u.get("avatar")} if u else None
            r["customer_name"] = str(r.get("customer_name") or (u["name"] if u else "Customer"))
            r["helpful_count"] = int(r.get("helpful_count") or 0)
            r["owner_reply"] = r.get("owner_reply")
            results.append(ReviewResponse(**r))
        return results

    async def add_review(
        self,
        business_id: str,
        data: ReviewIn,
        current_user: Dict[str, Any],
    ) -> ReviewResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        review_doc = {
            "id": new_id(),
            "business_id": business_id,
            "user_id": current_user["id"],
            "customer_name": current_user.get("name") or current_user.get("email") or "Customer",
            "rating": data.rating,
            "comment": data.comment,
            "helpful_count": 0,
            "owner_reply": None,
            "created_at": now_iso(),
        }
        await self.review_repo.add_or_replace_review(review_doc)

        # Recalculate business average rating
        all_r = await self.review_repo.get_all_by_business(business_id)
        avg = sum(r["rating"] for r in all_r) / len(all_r)
        await self.business_repo.update_rating(business_id, avg, len(all_r))

        # Notify business owner
        if biz.get("owner_id"):
            await self.notification_repo.create_notification({
                "id": new_id(),
                "user_id": biz["owner_id"],
                "title": "New Review",
                "body": f"{current_user['name']} left a {data.rating}-star review on '{biz['name']}'",
                "type": "review",
                "read": False,
                "created_at": now_iso(),
            })

        return ReviewResponse(**review_doc)

    async def list_my_reviews(self, current_user: Dict[str, Any]) -> List[ReviewResponse]:
        reviews = await self.review_repo.list_by_user(current_user["id"])
        results = []
        for r in reviews:
            b = await self.business_repo.get_by_id(r["business_id"])
            r["business"] = {
                "name": b["name"],
                "slug": b["slug"],
                "images": b.get("images", []),
            } if b else None
            r["customer_name"] = str(r.get("customer_name") or current_user.get("name") or "Customer")
            r["helpful_count"] = int(r.get("helpful_count") or 0)
            results.append(ReviewResponse(**r))
        return results

    async def list_owner_reviews(self, current_user: Dict[str, Any]) -> List[ReviewResponse]:
        """List all reviews across businesses owned by the current user."""
        biz_list = await self.business_repo.get_owner_businesses(current_user["id"])
        ids = [b["id"] for b in biz_list]
        reviews = await self.review_repo.list_by_business_ids(ids)
        results = []
        for r in reviews:
            u = await self.user_repo.get_by_id(r["user_id"])
            r["user"] = {"name": u["name"], "avatar": u.get("avatar")} if u else None
            r["customer_name"] = str(r.get("customer_name") or (u["name"] if u else "Customer"))
            r["helpful_count"] = int(r.get("helpful_count") or 0)
            r["owner_reply"] = r.get("owner_reply")
            results.append(ReviewResponse(**r))
        return results

    async def reply_review(
        self,
        review_id: str,
        reply: str,
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Post an owner reply to a review."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise NotFoundException("Review not found")
        
        biz = await self.business_repo.get_by_id(review["business_id"])
        if not biz:
            raise NotFoundException("Business not found")
        
        # Check ownership or admin
        if biz.get("owner_id") != current_user["id"] and current_user.get("role") != "admin":
            raise ForbiddenException("Only the business owner or admin can reply to this review")
        
        await self.review_repo.update_reply(review_id, reply)

        # Notify reviewer
        if review.get("user_id"):
            await self.notification_repo.create_notification({
                "id": new_id(),
                "user_id": review["user_id"],
                "title": "Owner replied to your review",
                "body": f"The owner of '{biz.get('name')}' replied: \"{reply[:50]}...\"",
                "type": "review_reply",
                "read": False,
                "created_at": now_iso(),
            })

        return {"message": "Reply posted successfully", "ok": True}

    async def delete_review(self, review_id: str, current_user: Dict[str, Any]) -> bool:
        r = await self.review_repo.get_by_id(review_id)
        if not r:
            raise NotFoundException("Review not found")
        if r["user_id"] != current_user["id"] and current_user["role"] != "admin":
            raise ForbiddenException("Forbidden")

        bid = r["business_id"]
        await self.review_repo.delete_by_id(review_id)

        # Recalculate rating
        all_r = await self.review_repo.get_all_by_business(bid)
        avg = (sum(x["rating"] for x in all_r) / len(all_r)) if all_r else 0.0
        await self.business_repo.update_rating(bid, avg, len(all_r))
        return True
