"""Main FastAPI application entry point with lifespan management, CORS, and routing."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import AppException
from app.database.mongodb import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
    mongo_manager,
)
from app.database.indexes import create_indexes
from app.database.seed import seed_database
from app.middleware.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.middleware.request_logging import RequestLoggingMiddleware
from app.api.router import api_router

# Configure root logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("infoez")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan managing startup and clean shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    try:
        await connect_to_mongo()
        db = get_database()
        await create_indexes(db)

        # Seed database if empty and ensure demo accounts have correct roles
        logger.info("Initializing database and verifying demo user credentials...")
        await seed_database(db)
    except Exception as e:
        logger.warning(f"Note on database initialization: {e}")

    yield

    logger.info("Application shutting down, closing resources...")
    await close_mongo_connection()
    logger.info("Shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Common development & local frontend origins
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
]

cors_origins = list(dict.fromkeys(DEFAULT_CORS_ORIGINS + [
    o for o in settings.cors_origins_list if o and o != "*"
]))

# Middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount API routers:
# 1. /api (100% backward-compatible with existing frontend & mobile Expo app)
# 2. /api/v1 (Modern versioned route support)
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")

# Direct root /health endpoint support
@app.get("/health", tags=["Health"])
async def root_health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database_fallback": mongo_manager.is_fallback,
    }
