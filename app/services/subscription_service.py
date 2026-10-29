"""Subscription service managing monetization tiers and user subscriptions."""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.core.constants import PLANS
from app.core.exceptions import BadRequestException
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.subscription import PlanResponse, SubscriptionResponse
from app.utils.datetime import new_id, now_iso

class SubscriptionService:
    def __init__(self, subscription_repo: SubscriptionRepository):
        self.subscription_repo = subscription_repo

    def get_plans(self) -> List[PlanResponse]:
        return [PlanResponse(**p) for p in PLANS]

    async def get_my_subscription(self, current_user: Dict[str, Any]) -> SubscriptionResponse:
        sub = await self.subscription_repo.get_by_user(current_user["id"])
        if not sub:
            return SubscriptionResponse(plan_id="free", plan_name="Free", status="active")
        return SubscriptionResponse(**sub)

    async def subscribe(
        self,
        plan_id: str,
        current_user: Dict[str, Any],
        payment_method: Optional[str] = "free",
        payment_reference: Optional[str] = None,
    ) -> SubscriptionResponse:
        plan = next((p for p in PLANS if p["id"] == plan_id), None)
        if not plan:
            raise BadRequestException("Invalid plan")

        now = datetime.now(timezone.utc)
        sub_doc = {
            "id": new_id(),
            "user_id": current_user["id"],
            "plan_id": plan["id"],
            "plan_name": plan["name"],
            "status": "active",
            "started_at": now.isoformat(),
            "renews_at": (now + timedelta(days=30)).isoformat(),
            "payment_method": payment_method or "free",
            "payment_reference": payment_reference,
        }
        await self.subscription_repo.save_subscription(current_user["id"], sub_doc)
        return SubscriptionResponse(**sub_doc)
