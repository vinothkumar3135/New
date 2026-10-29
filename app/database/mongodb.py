"""Async MongoDB connection and database management using Motor with resilient fallback."""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger("infoez.database")

class MongoManager:
    client: Optional[Any] = None
    db: Optional[Any] = None
    is_fallback: bool = False

mongo_manager = MongoManager()

async def connect_to_mongo() -> None:
    """Initialize Async MongoDB client, pinging database with in-memory fallback if server is offline."""
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGO_URL}...")
        client = AsyncIOMotorClient(
            settings.MONGO_URL,
            serverSelectionTimeoutMS=2000,
        )
        await client.admin.command("ping")
        mongo_manager.client = client
        mongo_manager.db = client[settings.DB_NAME]
        mongo_manager.is_fallback = False
        logger.info(f"Connected to database '{settings.DB_NAME}'.")
    except Exception as e:
        logger.warning(
            f"Could not connect to external MongoDB at {settings.MONGO_URL}: {e}. "
            "Activating in-memory database to allow application to run without disruption."
        )
        try:
            from mongomock_motor import AsyncMongoMockClient
            mock_client = AsyncMongoMockClient()
            mongo_manager.client = mock_client
            mongo_manager.db = mock_client[settings.DB_NAME]
            mongo_manager.is_fallback = True
            logger.info(f"In-memory MongoDB initialized for '{settings.DB_NAME}'.")
        except Exception as mock_err:
            logger.warning(f"Note: mongomock_motor fallback client unavailable ({mock_err}). Preserving connection reference.")
            mongo_manager.client = client
            mongo_manager.db = client[settings.DB_NAME]
            mongo_manager.is_fallback = False

async def close_mongo_connection() -> None:
    """Cleanly close MongoDB client connection."""
    if mongo_manager.client:
        logger.info("Closing MongoDB connection...")
        try:
            mongo_manager.client.close()
        except Exception:
            pass
        mongo_manager.client = None
        mongo_manager.db = None
        logger.info("MongoDB connection closed.")

def get_database() -> AsyncIOMotorDatabase:
    """Dependency / accessor for the active MongoDB database instance."""
    if mongo_manager.db is None:
        try:
            from mongomock_motor import AsyncMongoMockClient
            mongo_manager.client = AsyncMongoMockClient()
            mongo_manager.db = mongo_manager.client[settings.DB_NAME]
            mongo_manager.is_fallback = True
        except Exception:
            mongo_manager.client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=2000)
            mongo_manager.db = mongo_manager.client[settings.DB_NAME]
    return mongo_manager.db
