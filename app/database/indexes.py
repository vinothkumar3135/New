"""MongoDB index definitions and idempotent setup."""

import logging
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("infoez.indexes")

async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create all required MongoDB indexes idempotently."""
    try:
        # Users
        await db.users.create_index([("id", ASCENDING)], unique=True)
        await db.users.create_index([("email", ASCENDING)], unique=True)
        await db.users.create_index([("role", ASCENDING)])

        # Businesses
        await db.businesses.create_index([("id", ASCENDING)], unique=True)
        await db.businesses.create_index([("slug", ASCENDING)], unique=True)
        await db.businesses.create_index([("status", ASCENDING)])
        await db.businesses.create_index([("category_id", ASCENDING)])
        await db.businesses.create_index([("city", ASCENDING)])
        await db.businesses.create_index([("rating", DESCENDING)])
        await db.businesses.create_index([("featured", ASCENDING)])
        await db.businesses.create_index([("owner_id", ASCENDING)])
        await db.businesses.create_index([("lat", ASCENDING), ("lng", ASCENDING)])

        # Categories
        await db.categories.create_index([("id", ASCENDING)], unique=True)
        await db.categories.create_index([("slug", ASCENDING)], unique=True)

        # Reviews
        await db.reviews.create_index([("id", ASCENDING)], unique=True)
        await db.reviews.create_index([("business_id", ASCENDING)])
        await db.reviews.create_index([("user_id", ASCENDING)])
        await db.reviews.create_index([("business_id", ASCENDING), ("user_id", ASCENDING)])

        # Favorites
        await db.favorites.create_index([("user_id", ASCENDING), ("business_id", ASCENDING)], unique=True)

        # Enquiries
        await db.enquiries.create_index([("id", ASCENDING)], unique=True)
        await db.enquiries.create_index([("business_id", ASCENDING)])
        await db.enquiries.create_index([("user_id", ASCENDING)])

        # Claims
        await db.claims.create_index([("id", ASCENDING)], unique=True)
        await db.claims.create_index([("business_id", ASCENDING)])
        await db.claims.create_index([("user_id", ASCENDING)])

        # Notifications
        await db.notifications.create_index([("id", ASCENDING)], unique=True)
        await db.notifications.create_index([("user_id", ASCENDING)])
        await db.notifications.create_index([("user_id", ASCENDING), ("read", ASCENDING)])

        # Subscriptions
        await db.subscriptions.create_index([("user_id", ASCENDING)], unique=True)

        # Files
        await db.files.create_index([("id", ASCENDING)], unique=True)
        await db.files.create_index([("storage_path", ASCENDING)])

        logger.info("MongoDB indexes verified / created successfully.")
    except Exception as e:
        logger.warning(f"Note: MongoDB index creation reported: {e}")
