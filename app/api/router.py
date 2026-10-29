"""Master API Router combining all domain routers."""

from fastapi import APIRouter
from app.api.v1 import (
    auth_router,
    categories_router,
    businesses_router,
    reviews_router,
    favorites_router,
    enquiries_router,
    claims_router,
    subscriptions_router,
    notifications_router,
    users_router,
    uploads_router,
    health_router,
    analytics_router,
)

api_router = APIRouter()

# Include all domain routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(businesses_router)
api_router.include_router(reviews_router)
api_router.include_router(favorites_router)
api_router.include_router(enquiries_router)
api_router.include_router(claims_router)
api_router.include_router(subscriptions_router)
api_router.include_router(notifications_router)
api_router.include_router(users_router)
api_router.include_router(uploads_router)
api_router.include_router(analytics_router)
