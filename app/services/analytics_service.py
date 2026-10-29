from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from app.repositories.business_repository import BusinessRepository
from app.repositories.enquiry_repository import EnquiryRepository
from app.repositories.review_repository import ReviewRepository

class AnalyticsService:
    def __init__(
        self,
        business_repo: BusinessRepository,
        enquiry_repo: EnquiryRepository,
        review_repo: ReviewRepository,
    ):
        self.business_repo = business_repo
        self.enquiry_repo = enquiry_repo
        self.review_repo = review_repo

    async def get_owner_analytics(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Compute aggregate performance statistics for businesses owned by current user."""
        owner_id = current_user["id"]
        businesses = await self.business_repo.get_owner_businesses(owner_id)
        bids = [b["id"] for b in businesses]

        biz_count = len(businesses)
        avg_rating = (
            round(sum(float(b.get("rating", 0.0)) for b in businesses) / biz_count, 1)
            if biz_count > 0
            else 0.0
        )
        total_views = sum(int(b.get("view_count", 0)) for b in businesses)

        if not bids:
            return {
                "views": 0,
                "calls": 0,
                "whatsapp": 0,
                "directions": 0,
                "website": 0,
                "leads": 0,
                "enquiries": 0,
                "businesses": 0,
                "average_rating": 0.0,
            }

        leads = await self.enquiry_repo.list_by_business_ids(bids)
        lead_count = len(leads)

        # Aggregate tracked events
        db = self.business_repo.collection.database
        events = await db.events.find({"business_id": {"$in": bids}}).to_list(length=5000)
        call_count = sum(1 for e in events if e.get("kind") == "call")
        whatsapp_count = sum(1 for e in events if e.get("kind") == "whatsapp")
        direction_count = sum(1 for e in events if e.get("kind") == "direction")
        website_count = sum(1 for e in events if e.get("kind") == "website")

        # Include view events if view_count is greater
        view_event_count = sum(1 for e in events if e.get("kind") == "view")
        final_views = max(total_views, view_event_count)

        return {
            "views": final_views,
            "calls": call_count,
            "whatsapp": whatsapp_count,
            "directions": direction_count,
            "website": website_count,
            "leads": lead_count,
            "enquiries": lead_count,
            "businesses": biz_count,
            "average_rating": avg_rating,
        }

    async def get_owner_trends(self, current_user: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate 7-day trend metrics for the owner dashboard."""
        owner_id = current_user["id"]
        businesses = await self.business_repo.get_owner_businesses(owner_id)
        bids = [b["id"] for b in businesses]

        days_data = []
        today = datetime.now(timezone.utc)

        db = self.business_repo.collection.database
        events = (
            await db.events.find({"business_id": {"$in": bids}}).to_list(length=5000)
            if bids
            else []
        )

        for i in range(6, -1, -1):
            date_obj = today - timedelta(days=i)
            day_str = date_obj.strftime("%a")
            date_prefix = date_obj.strftime("%Y-%m-%d")

            day_events = [
                e for e in events if str(e.get("created_at", "")).startswith(date_prefix)
            ]
            day_views = sum(1 for e in day_events if e.get("kind") == "view")
            day_calls = sum(1 for e in day_events if e.get("kind") == "call")
            day_whatsapp = sum(1 for e in day_events if e.get("kind") == "whatsapp")

            days_data.append({
                "day": day_str,
                "views": day_views,
                "calls": day_calls,
                "whatsapp": day_whatsapp,
            })

        return {"days": days_data}
