"""Health check and database seeding API router."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.database.mongodb import get_database
from app.database.seed import seed_database

logger = logging.getLogger("infoez.health")

router = APIRouter(tags=["Health & Seed"])

@router.get("/")
async def root():
    """Root endpoint for status check matching existing frontend expectation."""
    return {"app": "Infoez API", "status": "ok"}

@router.get("/health")
async def health():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

@router.get("/health/database")
async def health_database(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Database connectivity health check."""
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "detail": str(e)},
        )

@router.post("/seed")
async def seed_data(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Idempotent database seeder endpoint."""
    return await seed_database(db)
