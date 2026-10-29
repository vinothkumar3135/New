"""V1 API Routers export."""

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.businesses import router as businesses_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.favorites import router as favorites_router
from app.api.v1.enquiries import router as enquiries_router
from app.api.v1.claims import router as claims_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.users import router as users_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.health import router as health_router
from app.api.v1.analytics import router as analytics_router

__all__ = [
    "auth_router",
    "categories_router",
    "businesses_router",
    "reviews_router",
    "favorites_router",
    "enquiries_router",
    "claims_router",
    "subscriptions_router",
    "notifications_router",
    "users_router",
    "uploads_router",
    "health_router",
    "analytics_router",
]
