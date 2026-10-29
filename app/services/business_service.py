"""Business service managing listings, search, nearby geo-queries, and moderation."""

import math
import re
from typing import Any, Dict, List, Optional
from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.business_repository import BusinessRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.enquiry_repository import EnquiryRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.business import (
    BusinessIn,
    BusinessUpdate,
    BusinessResponse,
    BusinessListResponse,
    BusinessDetailResponse,
)
from app.utils.datetime import new_id, now_iso
from app.utils.distance import haversine_distance
from app.utils.response import normalize_business
from app.utils.slug import slugify

class BusinessService:
    def __init__(
        self,
        business_repo: BusinessRepository,
        category_repo: CategoryRepository,
        favorite_repo: FavoriteRepository,
        review_repo: ReviewRepository,
        enquiry_repo: EnquiryRepository,
        notification_repo: NotificationRepository,
        user_repo: UserRepository,
    ):
        self.business_repo = business_repo
        self.category_repo = category_repo
        self.favorite_repo = favorite_repo
        self.review_repo = review_repo
        self.enquiry_repo = enquiry_repo
        self.notification_repo = notification_repo
        self.user_repo = user_repo

    async def list_businesses(
        self,
        q: Optional[str] = None,
        category_id: Optional[str] = None,
        city: Optional[str] = None,
        min_rating: Optional[float] = None,
        verified: Optional[bool] = None,
        sort: Optional[str] = None,
        featured: Optional[bool] = None,
        near_lat: Optional[float] = None,
        near_lng: Optional[float] = None,
        radius_km: Optional[float] = 25.0,
        include_pending: Optional[bool] = False,
        limit: int = 24,
        skip: int = 0,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> BusinessListResponse:
        query: Dict[str, Any] = {}

        # Visibility: only active by default; admin can request all via include_pending
        if not (include_pending and current_user and current_user.get("role") == "admin"):
            query["status"] = "active"

        if q:
            eq = re.escape(q.strip())
            query["$or"] = [
                {"name": {"$regex": eq, "$options": "i"}},
                {"description": {"$regex": eq, "$options": "i"}},
                {"services": {"$elemMatch": {"$regex": eq, "$options": "i"}}},
            ]

        if category_id:
            query["category_id"] = category_id
        if city:
            query["city"] = {"$regex": f"^{re.escape(city.strip())}$", "$options": "i"}
        if min_rating is not None:
            query["rating"] = {"$gte": min_rating}
        if verified is not None:
            query["verified"] = verified
        if featured:
            query["featured"] = True

        sort_spec = [("created_at", -1)]
        if sort == "rating":
            sort_spec = [("rating", -1), ("review_count", -1)]
        elif sort == "popular":
            sort_spec = [("view_count", -1), ("review_count", -1)]

        # Nearby geographic search
        if near_lat is not None and near_lng is not None:
            raw = await self.business_repo.find_many(query, sort=sort_spec, limit=500)
            with_dist = []
            target_radius = radius_km if radius_km is not None else 25.0
            for b in raw:
                lat = b.get("lat")
                lng = b.get("lng")
                if lat is None or lng is None:
                    continue
                d = haversine_distance(near_lat, near_lng, float(lat), float(lng))
                if d <= target_radius:
                    b["distance_km"] = round(d, 2)
                    with_dist.append(b)
            with_dist.sort(key=lambda x: x["distance_km"])
            paginated = with_dist[skip : skip + limit]
            items = [BusinessResponse(**normalize_business(x)) for x in paginated]
            pages = math.ceil(len(with_dist) / limit) if limit > 0 else 1
            return BusinessListResponse(items=items, total=len(with_dist), pages=pages)

        # Standard search
        raw_items = await self.business_repo.find_many(
            query,
            sort=sort_spec,
            skip=skip,
            limit=limit,
        )
        total = await self.business_repo.count_documents(query)
        items = [BusinessResponse(**normalize_business(x)) for x in raw_items]
        pages = math.ceil(total / limit) if limit > 0 else 1
        return BusinessListResponse(items=items, total=total, pages=pages)

    async def get_business_by_slug_or_id(
        self,
        identifier: str,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> BusinessDetailResponse:
        b = await self.business_repo.get_by_slug_or_id(identifier)
        if not b:
            raise NotFoundException("Business not found")

        # Increment view count in the background
        await self.business_repo.increment_view_count(b["id"])

        # Check if user favorited this business
        is_fav = False
        if current_user:
            is_fav = await self.favorite_repo.is_favorited(current_user["id"], b["id"])
        b["is_favorited"] = is_fav

        # Attach category object
        if b.get("category_id"):
            cat = await self.category_repo.get_by_id(b["category_id"])
            b["category"] = cat

        b_norm = normalize_business(b)
        b_resp = BusinessResponse(**b_norm)

        # Fetch reviews
        raw_reviews = await self.review_repo.list_by_business(b["id"])
        normalized_reviews = []
        for r in raw_reviews:
            r_clean = dict(r)
            r_clean.pop("_id", None)
            r_clean["customer_name"] = str(r_clean.get("customer_name") or (r_clean.get("user") or {}).get("name") or "Customer")
            r_clean["helpful_count"] = int(r_clean.get("helpful_count") or 0)
            normalized_reviews.append(r_clean)

        # Fetch similar businesses in the same category
        similar_raw = await self.business_repo.find_many(
            {"category_id": b.get("category_id"), "id": {"$ne": b["id"]}, "status": "active"},
            limit=4,
        )
        similar_items = [BusinessResponse(**normalize_business(s)) for s in similar_raw]

        return BusinessDetailResponse(
            **b_norm,
            business=b_resp,
            reviews=normalized_reviews,
            similar=similar_items,
        )

    async def create_business(
        self,
        data: BusinessIn,
        current_user: Dict[str, Any],
    ) -> BusinessResponse:
        slug_base = slugify(data.name)
        slug = slug_base
        i = 1
        while await self.business_repo.get_by_slug(slug):
            i += 1
            slug = f"{slug_base}-{i}"

        # Admin-created listings are auto-approved; owners land in pending queue
        status = "active" if current_user["role"] == "admin" else "pending"
        biz = {
            "id": new_id(),
            "owner_id": current_user["id"],
            "slug": slug,
            **data.model_dump(),
            "rating": 0.0,
            "review_count": 0,
            "view_count": 0,
            "verified": current_user["role"] == "admin",
            "featured": False,
            "status": status,
            "created_at": now_iso(),
        }
        await self.business_repo.create_business(biz)

        # Notify all admins on new pending listing
        if status == "pending":
            admins = await self.user_repo.get_admins()
            for a in admins:
                await self.notification_repo.create_notification({
                    "id": new_id(),
                    "user_id": a["id"],
                    "title": "New listing pending review",
                    "body": f"'{biz['name']}' by {current_user['name']} is awaiting approval.",
                    "type": "pending_listing",
                    "read": False,
                    "created_at": now_iso(),
                })

        return BusinessResponse(**normalize_business(biz))

    async def update_business(
        self,
        business_id: str,
        data: BusinessUpdate,
        current_user: Dict[str, Any],
    ) -> BusinessResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")
        if biz["owner_id"] != current_user["id"] and current_user["role"] != "admin":
            raise ForbiddenException("Not your business")

        upd = {k: v for k, v in data.model_dump().items() if v is not None}
        fresh = await self.business_repo.update_business(business_id, upd)
        return BusinessResponse(**normalize_business(fresh or biz))

    async def delete_business(
        self,
        business_id: str,
        current_user: Dict[str, Any],
    ) -> bool:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        await self.business_repo.delete_business(business_id)
        await self.review_repo.delete_by_business_id(business_id)
        await self.favorite_repo.delete_by_business_id(business_id)
        await self.enquiry_repo.delete_by_business_id(business_id)
        return True

    async def verify_business(self, business_id: str) -> BusinessResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        await self.business_repo.update_business(business_id, {"verified": True})
        await self.notification_repo.create_notification({
            "id": new_id(),
            "user_id": biz["owner_id"],
            "title": "Business Verified",
            "body": f"Your business '{biz['name']}' was verified by admin.",
            "type": "verified",
            "read": False,
            "created_at": now_iso(),
        })
        fresh = await self.business_repo.get_by_id(business_id)
        return BusinessResponse(**normalize_business(fresh or biz))

    async def approve_business(self, business_id: str) -> BusinessResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        await self.business_repo.update_business(business_id, {"status": "active"})
        await self.notification_repo.create_notification({
            "id": new_id(),
            "user_id": biz["owner_id"],
            "title": "Listing Approved",
            "body": f"Your listing '{biz['name']}' is now live on Infoez.",
            "type": "approved",
            "read": False,
            "created_at": now_iso(),
        })
        fresh = await self.business_repo.get_by_id(business_id)
        return BusinessResponse(**normalize_business(fresh or biz))

    async def reject_business(self, business_id: str, reason: str) -> BusinessResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        await self.business_repo.update_business(business_id, {"status": "rejected"})
        await self.notification_repo.create_notification({
            "id": new_id(),
            "user_id": biz["owner_id"],
            "title": "Listing Rejected",
            "body": f"Your listing '{biz['name']}' was rejected. Reason: {reason}",
            "type": "rejected",
            "read": False,
            "created_at": now_iso(),
        })
        fresh = await self.business_repo.get_by_id(business_id)
        return BusinessResponse(**normalize_business(fresh or biz))

    async def feature_business(self, business_id: str) -> BusinessResponse:
        biz = await self.business_repo.get_by_id(business_id)
        if not biz:
            raise NotFoundException("Business not found")

        new_val = not biz.get("featured", False)
        await self.business_repo.update_business(business_id, {"featured": new_val})
        fresh = await self.business_repo.get_by_id(business_id)
        return BusinessResponse(**normalize_business(fresh or biz))

    async def get_my_businesses(self, current_user: Dict[str, Any]) -> List[BusinessResponse]:
        docs = await self.business_repo.get_owner_businesses(current_user["id"])
        return [BusinessResponse(**normalize_business(b)) for b in docs]

    async def get_pending_businesses(self) -> List[Dict[str, Any]]:
        items = await self.business_repo.get_pending_businesses()
        for b in items:
            owner = await self.user_repo.get_by_id(b["owner_id"])
            b["owner"] = {"name": owner["name"], "email": owner["email"]} if owner else None
        return [normalize_business(b) for b in items]

    async def get_locations(self) -> List[Dict[str, Any]]:
        """Return all distinct cities and their associated areas across businesses."""
        businesses = await self.business_repo.find_many({"status": "active"}, limit=500)
        city_map: Dict[str, set] = {}
        for b in businesses:
            city = str(b.get("city") or "").strip()
            if not city:
                continue
            area = str(b.get("area") or "").strip()
            if not area and b.get("address"):
                area = str(b["address"]).split(",")[0].strip()
            if city not in city_map:
                city_map[city] = set()
            if area:
                city_map[city].add(area)

        defaults = {
            "Bangalore": ["Indiranagar", "Koramangala", "HSR Layout", "Whitefield", "Jayanagar", "MG Road"],
            "Mumbai": ["Bandra", "Andheri", "Colaba", "Juhu", "Powai", "BKC"],
            "Delhi": ["Connaught Place", "Hauz Khas", "Saket", "Karol Bagh", "Dwarka"],
            "Chennai": ["T. Nagar", "Adyar", "Anna Nagar", "Velachery", "Mylapore"],
            "Hyderabad": ["Banjara Hills", "Jubilee Hills", "Gachibowli", "Madhapur", "Hitec City"],
        }
        for def_city, def_areas in defaults.items():
            if def_city not in city_map:
                city_map[def_city] = set(def_areas)
            else:
                city_map[def_city].update(def_areas)

        return [
            {"city": c, "areas": sorted(list(areas))}
            for c, areas in sorted(city_map.items())
        ]

    async def track_event(self, business_id: str, kind: str) -> Dict[str, str]:
        """Track user events like call, view, whatsapp, direction, website."""
        if kind == "view":
            await self.business_repo.increment_view_count(business_id)
        
        # Record event in events collection
        db = self.business_repo.collection.database
        await db.events.insert_one({
            "id": new_id(),
            "business_id": business_id,
            "kind": kind,
            "created_at": now_iso(),
        })
        return {"tracked": kind}

    async def get_review_eligibility(self, business_id: str, current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check whether user is eligible to leave a review for this business."""
        if not current_user:
            return {"eligible": False, "reason": "authentication required"}
        
        existing = await self.review_repo.get_by_user_and_business(current_user["id"], business_id)
        if existing:
            return {"eligible": False, "reason": "already reviewed"}
        
        return {"eligible": True, "reason": None}
